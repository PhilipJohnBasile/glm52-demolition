#!/usr/bin/env python3
"""Plan per-layer expert bit-widths to spend the SAME memory budget more
intelligently. Uniform 3-bit wastes fidelity on robust layers and starves
sensitive ones. We allocate higher bits to the most sensitive layers and lower
to the rest, hitting a target average bit-width (= same size) but higher quality.

Sensitivity score per MoE layer:
  --mode depth     (default, no model needed) U-shaped: early + late layers are
                   most quantization-sensitive in transformers -> higher bits.
  --mode measured  (needs the pruned model) per-layer perplexity delta on the
                   calibration set: quantize one layer hard, measure damage.

Output: a plan.json {layer_idx: bits} consumed by 04_quantize.py --plan, plus the
realized average bits and estimated size so you can confirm it still fits.
"""

import argparse
import json
import math
import os


def depth_sensitivity(moe_layers):
    """U-shaped: highest at the two ends, lowest in the middle. Range ~[0,1]."""
    n = len(moe_layers)
    scores = {}
    for pos, li in enumerate(moe_layers):
        x = pos / max(n - 1, 1)           # 0..1 across MoE layers
        # symmetric U: 1 at ends, ~0 in middle
        scores[li] = (2 * abs(x - 0.5)) ** 1.5
    return scores


def allocate(scores, target_avg, spread=0.35, bit_choices=(2, 3, 4)):
    """Tiered allocation that keeps the average at target but creates real
    dynamic range: the most-sensitive `spread` fraction of layers get the high
    bit-width, the least-sensitive `spread` fraction get the low one, the middle
    stays at the baseline. Symmetric spread preserves the average.
    """
    layers = sorted(scores, key=lambda li: scores[li], reverse=True)
    if not layers:                 # no MoE layers (e.g. a fully-dense config) → empty plan, avoid div-by-zero below
        return {}
    n = len(layers)
    lo, hi = min(bit_choices), max(bit_choices)
    base = round(target_avg)
    plan = {li: base for li in layers}
    k = int(spread * n)
    for li in layers[:k]:          # most sensitive -> high bits
        plan[li] = hi
    for li in layers[-k:]:         # least sensitive -> low bits
        plan[li] = lo
    # correct any drift from target average by nudging middle layers
    mid = layers[k:n - k]
    cur = sum(plan.values()) / n
    i = 0
    while mid and abs(cur - target_avg) > 0.02 and i < len(mid):
        li = mid[i] if cur < target_avg else mid[-1 - i]
        step = 1 if cur < target_avg else -1
        nb = min(hi, max(lo, plan[li] + step))
        cur += (nb - plan[li]) / n
        plan[li] = nb
        i += 1
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="models/GLM-5.2-mxfp4/config.json")
    ap.add_argument("--mode", choices=["depth", "measured"], default="depth")
    ap.add_argument("--target-avg", type=float, default=3.0,
                    help="average expert bits (= memory budget); 3.0 ≈ 90GB plan")
    ap.add_argument("--keep-frac", type=float, default=0.30,
                    help="fraction of routed experts kept (for size estimate)")
    ap.add_argument("--spread", type=float, default=0.35,
                    help="fraction of layers pushed to each of hi/lo bits")
    ap.add_argument("--out", default="quant_plan.json")
    ap.add_argument("--bit-choices", default="2,3,4",
                    help="comma-separated bit options; use '3,4' to avoid lossy "
                         "PTQ 2-bit (needs QAT) while still protecting early/late layers")
    args = ap.parse_args()

    c = json.load(open(args.config))
    L = c["num_hidden_layers"]
    first_dense = c.get("first_k_dense_replace", 0) or 0
    freq = c.get("moe_layer_freq", 1) or 1
    moe_layers = [i for i in range(L)
                  if i >= first_dense and i % freq == 0]

    if args.mode == "measured":
        print("  [note] measured mode needs the pruned model; not yet built. "
              "Falling back to depth heuristic for the plan.")
    scores = depth_sensitivity(moe_layers)
    bit_choices = tuple(int(x) for x in args.bit_choices.split(","))
    plan = allocate(scores, args.target_avg, spread=args.spread, bit_choices=bit_choices)

    avg = sum(plan.values()) / len(plan)
    # size estimate (experts dominate): kept experts * GLU * avg_bits
    H, mi, ne, ns = (c["hidden_size"], c["moe_intermediate_size"],
                     c["n_routed_experts"], c.get("n_shared_experts", 0) or 0)
    glu = 3 * H * mi
    expert_bits = sum(b * ne * args.keep_frac * glu for b in plan.values())
    non_expert_gb = (ns * len(moe_layers) * glu * 6
                     + L * 4 * H * H * 6 + 2 * c["vocab_size"] * H * 6) / 8 / 1e9
    size_gb = expert_bits / 8 / 1e9 + non_expert_gb

    from collections import Counter
    json.dump({str(k): v for k, v in plan.items()}, open(args.out, "w"), indent=2)
    print(f"  MoE layers: {len(moe_layers)}  bit distribution: "
          f"{dict(sorted(Counter(plan.values()).items()))}")
    print(f"  realized avg expert bits: {avg:.2f} (target {args.target_avg})")
    print(f"  est. size @ keep={args.keep_frac:.0%}: ~{size_gb:.0f} GB")
    print(f"  wrote {args.out}  ->  04_quantize.py --plan {args.out}")


if __name__ == "__main__":
    main()
