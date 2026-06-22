#!/usr/bin/env python3
"""Apply the streamed REAP saliency: keep the top-K experts per MoE layer, slice
the pre-stacked switch_mlp/gate tensors, and write the pruned model — all
streamed one layer at a time so memory stays bounded (~5GB).

  python scripts/24_apply_prune.py --model models/GLM-5.2-mxfp4 \
      --saliency models/saliency.npz --ratio 0.70 --out models/GLM-5.2-pruned
"""

import argparse
import json
import os
import sys

import mlx.core as mx
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from weight_store import WeightStore  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/GLM-5.2-mxfp4")
    ap.add_argument("--saliency", default="models/saliency.npz")
    ap.add_argument("--ratio", type=float, default=0.70, help="fraction of experts to REMOVE")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg = json.load(open(os.path.join(args.model, "config.json")))
    ne = cfg["n_routed_experts"]
    keep = max(cfg["num_experts_per_tok"], round(ne * (1 - args.ratio)))
    ng = int(cfg.get("n_group", 1) or 1)
    if ng > 1:
        keep = max(ng, (keep // ng) * ng)          # group-valid (n_group=1 here -> no-op)
    print(f"  keeping {keep}/{ne} experts per MoE layer (remove {1-keep/ne:.0%})")

    sal = np.load(args.saliency)
    ws = WeightStore(args.model)
    os.makedirs(args.out, exist_ok=True)
    index = {}

    def save_shard(tensors, name):
        mx.save_safetensors(os.path.join(args.out, name), tensors)
        for k in tensors:
            index[k] = name

    # per-layer streaming: slice MoE experts, copy everything else
    L = cfg["num_hidden_layers"]
    moe = {i for i in range(L) if cfg["mlp_layer_types"][i] == "sparse"}
    for i in range(L):
        w = ws.load_prefix(ws.layer_prefix(i))
        if i in moe and str(i) in sal.files:
            s = sal[str(i)]
            keep_idx = mx.array(np.sort(np.argsort(s)[-keep:]))   # top-K experts
            for proj in ("gate_proj", "up_proj", "down_proj"):
                for suf in ("weight", "scales", "biases"):
                    k = f"model.layers.{i}.mlp.switch_mlp.{proj}.{suf}"
                    if k in w:
                        w[k] = mx.take(w[k], keep_idx, axis=0)
            gk = f"model.layers.{i}.mlp.gate.weight"
            if gk in w:
                w[gk] = mx.take(w[gk], keep_idx, axis=0)
            bk = f"model.layers.{i}.mlp.gate.e_score_correction_bias"
            if bk in w:
                w[bk] = mx.take(w[bk], keep_idx, axis=0)
        mx.eval(list(w.values()))
        save_shard(w, f"model-layer-{i:05d}.safetensors")
        del w
        mx.clear_cache()
        if i % 10 == 0:
            print(f"  layer {i}/{L} written")

    # non-layer tensors (embed, norm, lm_head)
    extra = {k: v for k, v in ws.load_prefix("model.embed_tokens.").items()}
    extra.update(ws.load_prefix("model.norm."))
    extra.update(ws.load_prefix("lm_head."))
    mx.eval(list(extra.values()))
    save_shard(extra, "model-extra.safetensors")

    # write index + config
    json.dump({"metadata": {}, "weight_map": index},
              open(os.path.join(args.out, "model.safetensors.index.json"), "w"))
    cfg["n_routed_experts"] = keep
    cfg["num_experts_per_tok"] = min(cfg["num_experts_per_tok"], keep)
    json.dump(cfg, open(os.path.join(args.out, "config.json"), "w"), indent=2)
    for fn in os.listdir(args.model):
        if "token" in fn.lower() or fn.endswith((".txt", ".jinja")):
            import shutil
            shutil.copy(os.path.join(args.model, fn), os.path.join(args.out, fn))
    print(f"  pruned model -> {args.out} (n_routed_experts={keep})")


if __name__ == "__main__":
    main()
