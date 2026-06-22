#!/usr/bin/env python3
"""Streaming RE-quantize: the pruned model is already mxfp4 (4.25-bit), so
mlx_lm.convert can't shrink it (it skips already-quantized modules). This streams
the model one layer at a time, dequantizes each quantized tensor (mxfp4 4-bit) and
re-quantizes to a smaller uniform affine format (default 3-bit), bounding memory to
~one layer (~5GB). Output ~85GB, loads with the glm_moe_dsa patch.

  python scripts/24b_stream_requantize.py --src models/GLM-5.2-pruned \
      --bits 3 --group-size 64 --out models/GLM-5.2-q3
"""

import argparse
import json
import os
import re
import sys

import mlx.core as mx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from weight_store import WeightStore  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="models/GLM-5.2-pruned")
    ap.add_argument("--bits", type=int, default=3, help="routed-expert bits (bulk)")
    ap.add_argument("--attn-bits", type=int, default=4,
                    help="attention bits (4 is stable+small; 3 NaNs)")
    ap.add_argument("--head-bits", type=int, default=6,
                    help="embed_tokens/lm_head bits — Unsloth Dynamic 2.0: keep these HIGH (cheap size, big quality)")
    ap.add_argument("--group-size", type=int, default=64)
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan", default=None,
                    help="per-layer expert bit plan json (04b_sensitivity_plan.py); "
                         "early/late layers get higher bits to stop long-gen Computation Collapse")
    ap.add_argument("--nvfp4", action="store_true",
                    help="use NVFP4 (group 16) for the 4-bit layers: ~half the error of 3-bit affine "
                         "+ the M5 Neural-Accelerator hardware path (~2x decode). 3-bit layers stay affine.")
    args = ap.parse_args()

    plan = {}
    if args.plan and os.path.exists(args.plan):
        plan = {int(k): v for k, v in json.load(open(args.plan)).items()}
        print(f"  per-layer plan: {len(plan)} layers, "
              f"avg {sum(plan.values()) / len(plan):.2f} bits "
              f"(experts default {args.bits}-bit where unlisted)")

    cfg = json.load(open(os.path.join(args.src, "config.json")))
    srcq = cfg["quantization"]            # mxfp4 group 32 bits 4
    ws = WeightStore(args.src)
    os.makedirs(args.out, exist_ok=True)
    index = {}

    overrides = {}   # module_path -> low-bit override (experts); collected for config

    def requant_group(w):
        """In-place mixed requant: routed EXPERTS (switch_mlp) -> low bits (3);
        attention/embed/lm_head/shared -> stable 6-bit (3-bit attention -> NaN).
        Returns nothing; records expert module paths in `overrides` for the config."""
        for sk in [k for k in w if k.endswith(".scales")]:
            base = sk[: -len(".scales")]                 # full module path
            wk, bk = base + ".weight", base + ".biases"
            deq = mx.dequantize(w[wk], w[sk], w.get(bk),
                                group_size=srcq["group_size"], bits=srcq["bits"],
                                mode=srcq.get("mode", "affine"))
            if "switch_mlp" in base:                       # routed expert -> per-layer plan, else uniform
                m = re.search(r"layers\.(\d+)\.", base)
                bits = plan.get(int(m.group(1)), args.bits) if m else args.bits
            elif "embed_tokens" in base or "lm_head" in base:
                bits = args.head_bits                      # Unsloth: embed/lm_head high-bit (cheap, big quality)
            else:
                bits = args.attn_bits                      # attention/shared stay stable
            # NVFP4 (group 16) for 4-bit layers: ~half the affine error + the M5 hardware path. 3-bit stays affine.
            if args.nvfp4 and bits == 4:
                gs, mode = 16, "nvfp4"
            else:
                gs, mode = args.group_size, "affine"
            q = mx.quantize(deq, group_size=gs, bits=bits, mode=mode)
            qw, qs = q[0], q[1]
            qb = q[2] if len(q) > 2 else None            # nvfp4/mxfp4 are scale-only (no biases); affine has 3
            w[wk], w[sk] = qw, qs
            bk2 = base + ".biases"
            if qb is not None:
                w[bk2] = qb
            elif bk2 in w:
                del w[bk2]                                # drop the stale affine bias when a layer switches to nvfp4
            if bits != args.attn_bits or mode != "affine":
                overrides[base] = {"group_size": gs, "bits": bits, "mode": mode}

    def save(w, name):
        mx.eval(list(w.values()))
        mx.save_safetensors(os.path.join(args.out, name), w)
        for k in w:
            index[k] = name

    L = cfg["num_hidden_layers"]
    for i in range(L):
        w = ws.load_prefix(ws.layer_prefix(i))
        requant_group(w)
        save(w, f"model-layer-{i:05d}.safetensors")
        del w
        mx.clear_cache()
        if i % 10 == 0:
            print(f"  layer {i}/{L} requantized")

    extra = {}
    for p in ("model.embed_tokens.", "model.norm.", "lm_head."):
        extra.update(ws.load_prefix(p))
    requant_group(extra)
    save(extra, "model-extra.safetensors")

    json.dump({"metadata": {}, "weight_map": index},
              open(os.path.join(args.out, "model.safetensors.index.json"), "w"))
    # mixed-precision config: default attn_bits (stable) + per-expert low-bit overrides
    q = {"group_size": args.group_size, "bits": args.attn_bits, "mode": "affine"}
    q.update(overrides)
    cfg["quantization"] = q
    print(f"  mixed quant: {len(overrides)} expert modules @ {args.bits}-bit, "
          f"rest @ {args.attn_bits}-bit")
    json.dump(cfg, open(os.path.join(args.out, "config.json"), "w"), indent=2)
    import shutil
    for fn in os.listdir(args.src):
        if "token" in fn.lower() or fn.endswith((".txt", ".jinja")):
            shutil.copy(os.path.join(args.src, fn), os.path.join(args.out, fn))
    print(f"  re-quantized -> {args.out} ({args.bits}-bit, group {args.group_size})")


if __name__ == "__main__":
    main()
