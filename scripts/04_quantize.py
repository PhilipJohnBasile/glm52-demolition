#!/usr/bin/env python3
"""Quantize the pruned GLM-5.2 to land under your RAM budget.

Two methods:

  --method rtn  (default) Mixed-precision round-to-nearest via mlx_lm.convert:
                routed experts low-bit, attention/gate/embeds safe-bit. Fast,
                no data needed. MLX's plain convert quantizes everything to one
                width and attention breaks at 2-bit, so we use a per-module
                predicate.

  --method dwq  Distilled Weight Quantization (mlx_lm dwq): distills the
                quantized student against the pruned model as TEACHER on the
                calibration data, recovering much of the quality lost at low
                bits. Uniform bit-width, but markedly better than RTN at 3-bit.
                Best quality-per-byte. Needs the calibration file + time.

DWQ teacher = the pruned model (which fits in memory after pruning); student =
the same at lower bits. Run AFTER 03_prune, using the same calibration set.
"""

import argparse
import os
import subprocess
import sys


def run_rtn(args):
    import json
    import re
    from mlx_lm.convert import convert

    # optional per-layer expert bit plan (from 04b_sensitivity_plan.py)
    plan = {}
    if args.plan and os.path.exists(args.plan):
        plan = {int(k): v for k, v in json.load(open(args.plan)).items()}
        print(f"  using per-layer plan: {len(plan)} layers, "
              f"avg {sum(plan.values())/len(plan):.2f} bits")

    def quant_predicate(path, module, config):
        """Return per-module quant params, or False to leave unquantized."""
        is_expert = "switch_mlp" in path  # routed experts (the bulk)
        # never quantize tiny/sensitive bits to the aggressive width
        sensitive = any(k in path for k in ("gate", "embed", "lm_head", "norm"))
        if not hasattr(module, "to_quantized"):
            return False
        if sensitive:
            return False  # leave in original precision
        if is_expert and plan:
            m = re.search(r"layers\.(\d+)\.", path)
            if m and int(m.group(1)) in plan:
                return {"group_size": args.group_size, "bits": plan[int(m.group(1))]}
        bits = args.bits_experts if is_expert else args.bits_rest
        return {"group_size": args.group_size, "bits": bits}

    print(f">> RTN mixed-precision: experts={args.bits_experts}-bit  "
          f"rest={args.bits_rest}-bit  group_size={args.group_size}")
    convert(args.src, mlx_path=args.dst, quantize=True,
            quant_predicate=quant_predicate)


def run_dwq(args):
    if not os.path.exists(args.data_path):
        sys.exit(f"  [stop] --method dwq needs calibration at {args.data_path} "
                 "(run 02_make_calibration.py first).")
    cmd = [sys.executable, "-m", "mlx_lm", "dwq",
           "--model", args.src,                  # teacher = pruned model
           "--mlx-path", args.dst,               # quantized student out
           "--bits", str(args.bits_experts),     # uniform target bits
           "--group-size", str(args.group_size),
           "--data-path", args.data_path,
           "--num-samples", str(args.num_samples),
           "--max-seq-length", "2048",
           "--batch-size", "1",
           "--grad-checkpoint"]
    print(f">> DWQ distilling {args.bits_experts}-bit student from {args.src}")
    print("   " + " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="models/GLM-5.2-pruned")
    ap.add_argument("--dst", default="models/GLM-5.2-demolished-mxmix")
    ap.add_argument("--method", choices=["rtn", "dwq"], default="rtn")
    ap.add_argument("--bits-experts", type=int, default=3)
    ap.add_argument("--bits-rest", type=int, default=6)
    ap.add_argument("--group-size", type=int, default=64)
    ap.add_argument("--plan", default=None,
                    help="per-layer expert bit plan json (04b_sensitivity_plan.py)")
    ap.add_argument("--data-path", default="calibration/calib.jsonl",
                    help="calibration for DWQ distillation")
    ap.add_argument("--num-samples", type=int, default=512)
    args = ap.parse_args()

    print(f">> Quantizing {args.src} -> {args.dst}  (method={args.method})")
    (run_dwq if args.method == "dwq" else run_rtn)(args)
    print(f">> Wrote {args.dst}")
    print(">> Check on-disk size:  du -sh", args.dst)


if __name__ == "__main__":
    main()
