#!/usr/bin/env python3
"""DSA index_topk sweep — the last single-stream speed lever (option A, #70).

The DSA keeps the top `index_topk` tokens in attention (default 2048 → it's FULL attention below 2048 ctx, so
the knob only bites on long contexts). Lower index_topk = fewer attention ops per decode step on long contexts.
This measures REAL decode tok/s at each index_topk on a long (>2048) context — verify-before-claim, because the
MoE expert-load is the known bottleneck and may dominate the attention saving (→ little/no gain). NOT lossless
(changes which tokens are attended), so a real deploy needs a quality check too; here we isolate the SPEED axis.

  python scripts/90_dsa_sweep.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import mlx.core as mx
import mlx_lm
from mlx_lm.models import cache as C

MODEL = os.path.join(os.path.dirname(__file__), "..", "models", "GLM-5.2-q3a4-v4")


def set_topk(model, topk):
    """Set index_topk on every layer that has a live DSA indexer; return the count."""
    n = 0
    for layer in model.model.layers:
        idx = getattr(layer.self_attn, "indexer", None)
        if idx is not None and hasattr(idx, "index_topk"):
            idx.index_topk = topk
            n += 1
    return n


def main():
    print(f"  loading {os.path.basename(MODEL)} …", flush=True)
    model, tok = mlx_lm.load(MODEL)
    seed = "def transform(x):\n    return x * 2 + 1  # one line of representative code\n" * 220
    ctx = tok.encode(seed)[:2600]                            # >2048 so the DSA sparsity actually engages
    n_idx = sum(1 for L in model.model.layers
                if getattr(L.self_attn, "indexer", None) is not None)
    print(f"  context = {len(ctx)} tokens | {n_idx} layers have a DSA indexer\n")
    N = 48
    base = None
    for topk in (2048, 1024, 512, 256):
        cnt = set_topk(model, topk)
        kv = C.make_prompt_cache(model)
        model(mx.array(ctx[:-1])[None], cache=kv)            # prefill the long context
        mx.eval([c.state for c in kv])
        y = mx.array(ctx[-1:], mx.uint32)
        t0 = time.time()
        for _ in range(N):
            y = mx.argmax(model(y[None], cache=kv)[0, -1:], axis=-1)
            mx.eval(y)
        dt = time.time() - t0
        tps = N / dt
        base = base or tps
        print(f"  index_topk={topk:5d} ({cnt} indexers set): {tps:5.1f} tok/s  ({tps / base:.2f}x vs 2048)  [{dt:.1f}s]")
    print("\n  → if ~flat, the MoE expert-load dominates (attention isn't the bottleneck) → dsa knob is a no-op here.")


if __name__ == "__main__":
    main()
