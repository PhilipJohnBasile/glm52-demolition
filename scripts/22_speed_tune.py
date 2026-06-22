#!/usr/bin/env python3
"""Speed tuner — reduce ACTIVE experts per token (num_experts_per_tok). Decode is
memory-bandwidth-bound on the active expert weights, so fewer active experts ≈
proportionally faster decode. Set this BEFORE pruning/healing so Router-KD + the
heal adapt the router to the new top-k (otherwise quality drops).

  python scripts/22_speed_tune.py --model models/GLM-5.2-mxfp4 --topk 6
  # then prune -> router-kd -> heal as usual; the model is adapted to topk=6.
"""

import argparse
import json
import os
import shutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--topk", type=int, default=6,
                    help="new num_experts_per_tok (default 8 in GLM-5.2)")
    args = ap.parse_args()

    cfgp = os.path.join(args.model, "config.json")
    cfg = json.load(open(cfgp))
    old = cfg.get("num_experts_per_tok")
    if old is None:
        raise SystemExit("  config has no num_experts_per_tok (not an MoE?)")
    if args.topk >= old:
        raise SystemExit(f"  --topk {args.topk} must be < current {old}")

    shutil.copy(cfgp, cfgp + ".bak")
    cfg["num_experts_per_tok"] = args.topk
    json.dump(cfg, open(cfgp, "w"), indent=2)
    speedup = old / args.topk
    print(f"  num_experts_per_tok: {old} -> {args.topk}")
    print(f"  ~{(1 - args.topk/old)*100:.0f}% fewer active expert bytes/token "
          f"-> ~{speedup:.2f}x decode headroom (bandwidth-bound)")
    print(f"  backup: {cfgp}.bak")
    print("  IMPORTANT: run prune -> 21_router_kd -> heal so the router ADAPTS to "
          "the new top-k. Eval (07) to confirm the quality trade is worth it.")


if __name__ == "__main__":
    main()
