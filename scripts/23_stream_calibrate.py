#!/usr/bin/env python3
"""STREAMING REAP calibration — produces per-expert saliency for a >RAM model on
128GB, by reading the model ONCE, one ~5GB layer at a time (never resident whole).

This is the free path that makes pruning GLM-5.2 possible on a 128GB Mac: the
naive mmap forward OOMs at ~120GB, but here the working set is ~one layer (~5GB)
plus the calibration hidden states. We forward the whole calibration batch through
each layer in turn, capture the router's gate scores per expert (router-weighted
saliency = the REAP signal), then free the layer and move on.

  python scripts/23_stream_calibrate.py --model models/GLM-5.2-mxfp4 \
      --data heal/mine/verified.jsonl --n 128 --seq 1024 --out models/saliency.npz

Output: saliency.npz {layer_idx: [n_routed_experts] saliency}. Feed to
24_apply_prune.py to slice the kept experts and write the pruned model.
"""

import argparse
import json
import os
import sys
import time

import mlx.core as mx
import mlx.nn as nn
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from weight_store import WeightStore  # noqa: E402
from mlx_lm.models.glm_moe_dsa import ModelArgs, GlmDsaDecoderLayer  # noqa: E402
from mlx_lm.models import deepseek_v32 as dsv32  # noqa: E402


def quantize_into(module, weights, q):
    """Quantize the modules that have .scales in `weights`, then load them."""
    def pred(path, mod):
        return f"{path}.scales" in weights
    nn.quantize(module, group_size=q["group_size"], bits=q["bits"],
                mode=q["mode"], class_predicate=pred)
    module.load_weights(list(weights.items()), strict=False)
    mx.eval(module.parameters())


def strip(w, prefix):
    return {k[len(prefix):]: v for k, v in w.items() if k.startswith(prefix)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/GLM-5.2-mxfp4")
    ap.add_argument("--data", default="heal/mine/verified.jsonl")
    ap.add_argument("--n", type=int, default=128, help="num calibration sequences")
    ap.add_argument("--seq", type=int, default=1024, help="tokens per sequence")
    ap.add_argument("--batch", type=int, default=16, help="seqs per micro-batch")
    ap.add_argument("--max-layers", type=int, default=0, help="cap layers (0=all; for testing)")
    ap.add_argument("--out", default="models/saliency.npz")
    args = ap.parse_args()

    cfg = json.load(open(os.path.join(args.model, "config.json")))
    margs = ModelArgs.from_dict(cfg)
    q = cfg["quantization"]
    ws = WeightStore(args.model)
    ne = cfg["n_routed_experts"]
    L = cfg["num_hidden_layers"]

    # tokenizer
    from mlx_lm import load as _load  # only for tokenizer (lazy, tiny use)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)

    # calibration text -> token sequences
    texts = []
    for line in open(args.data):
        if len(texts) >= args.n:
            break
        o = json.loads(line)
        t = o.get("text") or "\n".join(m.get("content", "") for m in o.get("messages", []))
        if t and t.strip():
            texts.append(t)
    seqs = []
    for t in texts:
        ids = tok.encode(t)[: args.seq]
        if len(ids) >= 16:
            seqs.append(ids + [tok.pad_token_id or 0] * (args.seq - len(ids)))
    seqs = mx.array(seqs[: args.n])
    print(f"  calibration: {seqs.shape[0]} seqs x {seqs.shape[1]} tokens")

    saliency = {i: np.zeros(ne, dtype=np.float64) for i in range(L)
                if cfg["mlp_layer_types"][i] == "sparse"}
    pad_id = tok.pad_token_id or 0

    # ---- embed (streamed) ----
    embed_w = strip(ws.load_prefix("model.embed_tokens."), "model.embed_tokens.")
    # nn.quantize won't quantize a ROOT Embedding, so dequantize it manually.
    if "scales" in embed_w:
        deq = mx.dequantize(embed_w["weight"], embed_w["scales"],
                            embed_w.get("biases"), group_size=q["group_size"],
                            bits=q["bits"], mode=q["mode"])
    else:
        deq = embed_w["weight"]
    embed = nn.Embedding(cfg["vocab_size"], cfg["hidden_size"])
    embed.weight = deq
    mx.eval(embed.weight)
    del embed_w

    t0 = time.time()
    # process micro-batches; for each, stream through all layers once
    for b0 in range(0, seqs.shape[0], args.batch):
        batch = seqs[b0:b0 + args.batch]
        H = embed(batch)
        mask = dsv32.create_attention_mask(H, None, return_array=True)
        shared_topk = None
        n_layers = min(L, args.max_layers) if args.max_layers else L
        for i in range(n_layers):
            lw = strip(ws.load_prefix(ws.layer_prefix(i)), ws.layer_prefix(i))
            layer = GlmDsaDecoderLayer(margs, i)
            quantize_into(layer, lw, q)
            del lw

            r, topk = layer.self_attn(layer.input_layernorm(H), mask, None, shared_topk)
            if layer.is_full:
                shared_topk = topk
            H = H + r
            x = layer.post_attention_layernorm(H)
            mlp = layer.mlp
            if isinstance(mlp, dsv32.DeepseekV32MoE):
                inds, scores = mlp.gate(x)
                y = mlp.switch_mlp(x, inds)            # [b,s,top_k,hidden]
                # TRUE REAP saliency = router_weight × activation_norm (not just
                # frequency). + padding mask so pad tokens don't corrupt it.
                norms = mx.sqrt((y.astype(mx.float32) ** 2).sum(axis=-1) + 1e-12)
                contrib = scores * norms              # [b,s,top_k]
                mx.eval(inds, contrib)
                tk = inds.shape[-1]
                real = np.array(batch != pad_id).reshape(-1)        # [b*s]
                ii = np.array(inds).reshape(-1, tk)[real]
                cc = np.nan_to_num(np.array(contrib).reshape(-1, tk)[real],
                                   nan=0.0, posinf=0.0, neginf=0.0).astype(np.float64)
                np.add.at(saliency[i], ii.reshape(-1), cc.reshape(-1))
                y = (y * scores[..., None]).sum(axis=-2).astype(H.dtype)
                if mlp.config.n_shared_experts is not None:
                    y = y + mlp.shared_experts(x)
                H = H + y
            else:
                H = H + mlp(x)
            mx.eval(H)
            del layer
            mx.clear_cache()
        print(f"  batch {b0//args.batch + 1}: done ({time.time()-t0:.0f}s elapsed)")

    np.savez(args.out, **{str(k): v for k, v in saliency.items()})
    nz = {k: int((v > 0).sum()) for k, v in list(saliency.items())[:3]}
    print(f"  saved saliency -> {args.out} ({len(saliency)} MoE layers)")
    print(f"  sample active-expert counts (first layers): {nz}")
    print(f"  total time {time.time()-t0:.0f}s — next: scripts/24_apply_prune.py")


if __name__ == "__main__":
    main()
