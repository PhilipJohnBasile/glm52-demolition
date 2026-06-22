#!/usr/bin/env python3
"""Router-KD — the cheapest, most MoE-specific healer. After pruning, the router
still scores experts as if the pruned ones existed, so its routing is miscalibrated.
This recalibrates ONLY the router/gate parameters (experts frozen), which the
research shows recovers a lot for tiny cost ("Necessity of Router Calibration",
arXiv 2603.02217). Run it FIRST (before SFT/KD), on the pruned model.

  python scripts/21_router_kd.py --model models/GLM-5.2-pruned \
      --data calibration/calib.jsonl --out models/GLM-5.2-pruned-routercal --iters 300
"""

import argparse
import glob
import json
import os
import shutil
import sys

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
from mlx.utils import tree_flatten
from mlx_lm import load

HERE = os.path.dirname(__file__)


def find_gates(model):
    """Return the router/gate modules across MoE layers (deepseek_v32 / qwen3)."""
    # locate decoder layers
    layers = None
    for path in (("model", "layers"), ("layers",), ("model", "model", "layers")):
        obj = model
        for a in path:
            obj = getattr(obj, a, None)
            if obj is None:
                break
        if obj is not None:
            layers = obj
            break
    if layers is None:
        sys.exit("  [stop] could not find decoder layers")
    gates = []
    for layer in layers:
        mlp = getattr(layer, "mlp", None) or getattr(layer, "feed_forward", None)
        gate = getattr(mlp, "gate", None) if mlp else None
        if gate is not None and hasattr(gate, "weight"):
            gates.append(gate)
    return gates


def _texts(path, n):
    out = []
    for line in open(path):
        if len(out) >= n:
            break
        o = json.loads(line)
        out.append(o.get("text") or "\n".join(
            m.get("content", "") for m in o.get("messages", [])))
    return [t for t in out if t and t.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", default="calibration/calib.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--max", type=int, default=400)
    ap.add_argument("--max-seq", type=int, default=1024)
    ap.add_argument("--learning-rate", type=float, default=1e-4)
    args = ap.parse_args()

    model, tok = load(args.model)
    model.freeze()                                  # freeze EVERYTHING
    gates = find_gates(model)
    if not gates:
        sys.exit("  [stop] no MoE router/gate modules found (is this an MoE?)")
    for g in gates:
        g.unfreeze()                                # ... then ONLY the routers
    n_train = sum(v.size for _, v in tree_flatten(model.trainable_parameters()))
    print(f"  {len(gates)} routers; trainable params: {n_train/1e6:.3f}M "
          f"(tiny — that's the point)")

    texts = _texts(args.data, args.max)
    if not texts:
        sys.exit(f"  [stop] no calibration text in {args.data}")
    opt = optim.Adam(learning_rate=args.learning_rate)

    def loss_fn(model, ids):
        logits = model(ids[:, :-1])
        targets = ids[:, 1:]
        return nn.losses.cross_entropy(logits, targets, reduction="mean")

    lg = nn.value_and_grad(model, loss_fn)
    step = 0
    while step < args.iters:
        for t in texts:
            if step >= args.iters:
                break
            ids = tok.encode(t)[: args.max_seq]
            if len(ids) < 4:
                continue
            x = mx.array([ids])
            loss, grads = lg(model, x)
            opt.update(model, grads)
            mx.eval(model.parameters(), opt.state, loss)
            if step % 25 == 0:
                print(f"  step {step:4}  LM loss {loss.item():.4f}")
            step += 1

    # save the router-recalibrated model (full weights + config/tokenizer)
    os.makedirs(args.out, exist_ok=True)
    weights = dict(tree_flatten(model.parameters()))
    mx.save_safetensors(os.path.join(args.out, "model.safetensors"), weights)
    for fn in os.listdir(args.model):
        if fn.endswith((".json", ".txt")) or "token" in fn.lower():
            shutil.copy(os.path.join(args.model, fn), os.path.join(args.out, fn))
    print(f"  router-recalibrated model -> {args.out}")
    print("  next: quantize (04) then SFT/KD heal (06/20).")


if __name__ == "__main__":
    main()
