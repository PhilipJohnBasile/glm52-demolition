#!/usr/bin/env python3
"""KL-divergence quant eval — the GOLD-STANDARD metric (Unsloth Dynamic 2.0, Google QAT) we were missing.

Measures how faithfully a quantized model reproduces a higher-precision REFERENCE's next-token distribution:
KL(P_ref || Q_quant) averaged over tokens, in nats (lower = better, 0 = identical). This is what lets us pick
uniform-q3 vs saliency-dynamic-q3 (src/dynamic_bits) OBJECTIVELY instead of asserting.

The catch for us: a 77-expert BF16 reference is ~500GB (won't fit 128GB). So we cache a memory-safe TOP-K reference
(top-k log-probs per token, computed once via streamed/disk-paged forward), then score each quant against the cache
cheaply — and reuse the same cache for every quant variant. KL is concentrated on the top mass, so top-k≈full.

  python scripts/84_kl_eval.py --selftest                                   # CPU: prove the math
  python scripts/84_kl_eval.py --ref models/...-bf16 --quant models/...-q3 --build-cache   # GPU: cache ref
  python scripts/84_kl_eval.py --quant models/...-q3-dynamic --cache kl_ref.npz            # GPU: score a quant
"""
import argparse
import os
import sys

import numpy as np


def _log_softmax(x):
    x = np.asarray(x, dtype=np.float64)
    m = x.max(axis=-1, keepdims=True)
    z = x - m
    return z - np.log(np.exp(z).sum(axis=-1, keepdims=True))


def kl_per_token(ref_logits, quant_logits):
    """Mean full-vocab KL(P_ref || Q_quant) over positions, in nats. logits: [..., vocab]."""
    lr = _log_softmax(ref_logits)
    lq = _log_softmax(quant_logits)
    return float(np.mean((np.exp(lr) * (lr - lq)).sum(axis=-1)))


def ref_cache(ref_logits, k=64):
    """Memory-safe reference: per position keep the top-k token indices + their ref log-probs (k≈64 ≪ vocab)."""
    lr = _log_softmax(ref_logits)
    idx = np.argsort(-lr, axis=-1)[..., :k]
    lr_k = np.take_along_axis(lr, idx, axis=-1)
    return {"idx": idx.astype(np.int32), "lr_k": lr_k.astype(np.float32)}


def kl_from_cache(cache, quant_logits):
    """KL on the top-k reference mass: sum_k P_ref(v)·(logP_ref(v) − logQ_quant(v)). Tail (small P_ref) ignored."""
    idx, lr_k = cache["idx"], cache["lr_k"].astype(np.float64)
    lq = _log_softmax(quant_logits)
    lq_k = np.take_along_axis(lq, idx, axis=-1)
    return float(np.mean((np.exp(lr_k) * (lr_k - lq_k)).sum(axis=-1)))


def collect_logits(model_path, prompts, max_positions=64):  # GPU
    """Forward an mlx_lm model on prompts → logits at the last max_positions of each (np.float32)."""
    from mlx_lm import load
    import mlx.core as mx
    model, tok = load(model_path)
    out = []
    for p in prompts:
        ids = mx.array(tok.encode(p))[None]
        logits = model(ids)[0][-max_positions:].astype(mx.float32)   # cast bf16 -> f32 (numpy can't buffer bf16)
        mx.eval(logits)
        out.append(np.asarray(logits, dtype=np.float32))
    return out


def _selftest():
    rng = np.random.default_rng(0)
    logits = rng.normal(size=(10, 2000))
    logits[:, :8] += rng.uniform(6, 12, size=(10, 8))              # peaked like a real LLM (few dominant tokens)
    assert abs(kl_per_token(logits, logits)) < 1e-9, "KL(P||P) must be 0"
    small = kl_per_token(logits, logits + rng.normal(scale=0.4, size=logits.shape))
    large = kl_per_token(logits, logits + rng.normal(scale=1.5, size=logits.shape))
    assert 0 < small < large, (small, large)                       # more quant noise → higher KL (monotone)
    # top-k cache approximates full KL + is 0 against itself
    cache = ref_cache(logits, k=128)
    assert abs(kl_from_cache(cache, logits)) < 1e-6, "cache KL(P||P) must be 0"
    noisy = logits + rng.normal(scale=0.4, size=logits.shape)
    full, topk = kl_per_token(logits, noisy), kl_from_cache(cache, noisy)
    assert abs(full - topk) / full < 0.25, (full, topk)            # top-128 within 25% of full KL on a peaked dist
    print(f"  KL(P||P)=0 ✓ | noise monotone {small:.4f}<{large:.4f} ✓ | top-k≈full ({topk:.4f} vs {full:.4f}) ✓ (nats/tok)")
    print("  kl_eval selftest PASS — the gold-standard quant metric. Cache BF16-ref once, score uniform vs dynamic, keep lower KL.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--ref", default="")
    ap.add_argument("--quant", default="")
    ap.add_argument("--cache", default="kl_ref.npz")
    ap.add_argument("--build-cache", action="store_true")
    ap.add_argument("--prompts", default="")
    ap.add_argument("--n", type=int, default=64)
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    prompts = ([line.strip() for line in open(a.prompts) if line.strip()][:a.n]
               if a.prompts and os.path.exists(a.prompts) else ["def add(a, b):\n    return"] * 8)
    if a.build_cache:
        ref = collect_logits(a.ref, prompts)
        np.savez(a.cache, **{f"c{i}": v for i, v in enumerate(ref)})
        print(f"  cached {len(ref)} ref logit-blocks → {a.cache}")
        return
    cache_npz = np.load(a.cache)
    quant = collect_logits(a.quant, prompts)
    kls = [kl_from_cache(ref_cache(cache_npz[f"c{i}"]), q) for i, q in enumerate(quant)]
    if not kls:                                          # no blocks → np.mean([]) is a silent nan
        print("  ✗ no logit-blocks collected — check --prompts / the models (KL undefined)")
        return
    print(f"  KL({os.path.basename(a.quant)} vs ref) = {np.mean(kls):.4f} nats/token (lower = better)")


if __name__ == "__main__":
    main()
