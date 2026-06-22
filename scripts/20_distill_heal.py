#!/usr/bin/env python3
"""Logit-KD distillation heal — the strongest recovery method (Recover-LoRA /
expert-wise KD). Trains LoRA adapters on the pruned student to match a TEACHER's
logit distribution via forward KL, which the research shows beats plain SFT.

128 GB-safe via OFFLINE teacher logits — never hold teacher + student together:
  1. dump : run the TEACHER alone over prompts, save top-k logits to disk.
  2. train: load the STUDENT alone, train LoRA to match those logits (forward KL).

Teacher choice (must fit alone): for ITERATIVE pruning, the teacher is the
previous, less-pruned stage (SlimMoE-style). For one-shot, the best local teacher
is the pruned-but-unquantized model (recovers quant loss).

  # 1) dump teacher logits
  python scripts/20_distill_heal.py dump --teacher <model> \
      --data heal/data/train.jsonl --out heal/logits --topk 64 --max 400
  # 2) distill the student against them
  python scripts/20_distill_heal.py train --student <pruned-model> \
      --logits heal/logits --adapter heal/adapters-kd --iters 800
"""

import argparse
import glob
import json
import os
import sys

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
from mlx.utils import tree_flatten
from mlx_lm import load
from mlx_lm.tuner.utils import linear_to_lora_layers

HERE = os.path.dirname(__file__)


def _texts(path, n):
    out = []
    for line in open(path):
        if len(out) >= n:
            break
        o = json.loads(line)
        if "messages" in o:                      # render chat to a flat string
            out.append("\n".join(m.get("content", "") for m in o["messages"]))
        elif "text" in o:
            out.append(o["text"])
    return out


def dump(args):
    """Teacher forward -> save top-k logits per position (compact)."""
    model, tok = load(args.teacher)
    os.makedirs(args.out, exist_ok=True)
    texts = _texts(args.data, args.max)
    saved = 0
    for i, t in enumerate(texts):
        ids = tok.encode(t)[: args.max_seq]
        if len(ids) < 4:
            continue
        x = mx.array([ids])
        logits = model(x)[0]                      # [seq, vocab]
        k = min(args.topk, logits.shape[-1])
        idx = mx.argpartition(logits, -k, axis=-1)[:, -k:]   # [seq, k]
        vals = mx.take_along_axis(logits, idx, axis=-1)      # [seq, k]
        mx.eval(idx, vals)
        mx.savez(os.path.join(args.out, f"ex_{i}.npz"),
                 ids=mx.array(ids), idx=idx, vals=vals)
        saved += 1
        if saved % 50 == 0:
            print(f"  dumped {saved}/{len(texts)}")
    json.dump({"topk": args.topk, "count": saved},
              open(os.path.join(args.out, "meta.json"), "w"))
    print(f"  teacher logits saved: {saved} -> {args.out}")


def kl_loss(student_logits, idx, teacher_vals, temp):
    """Forward KL over the teacher's top-k tokens (temperature-scaled, xT^2)."""
    s_top = mx.take_along_axis(student_logits, idx, axis=-1) / temp   # [seq,k]
    t_logp = nn.log_softmax(teacher_vals / temp, axis=-1)
    s_logp = nn.log_softmax(s_top, axis=-1)
    t_p = mx.exp(t_logp)
    kl = (t_p * (t_logp - s_logp)).sum(axis=-1)                       # [seq]
    return kl.mean() * (temp * temp)


def train(args):
    model, tok = load(args.student)
    model.freeze()
    linear_to_lora_layers(
        model, args.num_layers,
        {"rank": args.rank, "scale": args.scale, "dropout": 0.05})
    files = sorted(glob.glob(os.path.join(args.logits, "ex_*.npz")))
    if not files:
        sys.exit(f"  [stop] no logits in {args.logits} (run `dump` first)")
    print(f"  {len(files)} teacher samples; trainable params: "
          f"{sum(v.size for _, v in tree_flatten(model.trainable_parameters()))/1e6:.2f}M")

    opt = optim.Adam(learning_rate=args.learning_rate)

    def loss_fn(model, ids, idx, vals):
        logits = model(ids[None])[0]
        return kl_loss(logits, idx, vals, args.temp)

    lg = nn.value_and_grad(model, loss_fn)
    step = 0
    while step < args.iters:
        for f in files:
            if step >= args.iters:
                break
            d = mx.load(f)
            loss, grads = lg(model, d["ids"], d["idx"], d["vals"])
            opt.update(model, grads)
            mx.eval(model.parameters(), opt.state, loss)
            if step % 25 == 0:
                print(f"  step {step:4}  KL loss {loss.item():.4f}")
            step += 1

    os.makedirs(args.adapter, exist_ok=True)
    adapter_weights = dict(tree_flatten(model.trainable_parameters()))
    mx.save_safetensors(os.path.join(args.adapter, "adapters.safetensors"),
                        adapter_weights)
    json.dump({"fine_tune_type": "lora", "num_layers": args.num_layers,
               "lora_parameters": {"rank": args.rank, "scale": args.scale,
                                   "dropout": 0.05}},
              open(os.path.join(args.adapter, "adapter_config.json"), "w"))
    print(f"  KD-healed adapters -> {args.adapter}")
    print(f"  serve: mlx_lm.server --model {args.student} --adapter-path {args.adapter}")


def rollout(args):
    """ON-POLICY data: the STUDENT generates completions for the task prompts, so the
    teacher later corrects the student where IT actually errs (far more sample-efficient
    than offline KD on a fixed corpus — the GLM-5 recipe). Writes chat JSONL that the
    existing `dump` (teacher logits) + `train` (forward-KL) phases consume unchanged."""
    from mlx_lm.models.cache import make_prompt_cache
    model, tok = load(args.student, adapter_path=args.adapter)
    tasks = [json.loads(l) for l in open(args.tasks) if l.strip()][: args.max]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    n = 0
    with open(args.out, "w") as f:
        for t in tasks:
            prompt = t.get("prompt") or t.get("text", "")
            ids = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                          add_generation_prompt=True, tokenize=True)
            cache = make_prompt_cache(model)                       # our make_cache fix
            logits = model(mx.array([ids]), cache=cache)[0, -1]
            out = []
            for _ in range(args.max_tokens):
                tid = (int(mx.random.categorical(logits / args.temp).item()) if args.temp > 0
                       else int(mx.argmax(logits).item()))
                if tid == tok.eos_token_id:
                    break
                out.append(tid)
                logits = model(mx.array([[tid]]), cache=cache)[0, -1]
            f.write(json.dumps({"messages": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": tok.decode(out)}]}) + "\n")
            n += 1
            if n % 10 == 0:
                print(f"  rolled out {n}/{len(tasks)}", flush=True)
    print(f"  on-policy rollouts -> {args.out}  ({n} ex). Next: `dump` teacher logits on "
          "this file (teacher = the higher-precision pruned-v2), then `train`.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rollout")
    r.add_argument("--student", required=True)
    r.add_argument("--adapter", default="heal/adapters-grpo")
    r.add_argument("--tasks", default="eval/tasks.jsonl")
    r.add_argument("--out", default="heal/data/onpolicy.jsonl")
    r.add_argument("--max", type=int, default=200)
    r.add_argument("--max-tokens", type=int, default=400)
    r.add_argument("--temp", type=float, default=0.8)
    r.set_defaults(func=rollout)
    d = sub.add_parser("dump")
    d.add_argument("--teacher", required=True)
    d.add_argument("--data", default="heal/data/train.jsonl")
    d.add_argument("--out", default="heal/logits")
    d.add_argument("--topk", type=int, default=64)
    d.add_argument("--max", type=int, default=400)
    d.add_argument("--max-seq", type=int, default=2048)
    d.set_defaults(func=dump)
    t = sub.add_parser("train")
    t.add_argument("--student", required=True)
    t.add_argument("--logits", default="heal/logits")
    t.add_argument("--adapter", default="heal/adapters-kd")
    t.add_argument("--iters", type=int, default=800)
    t.add_argument("--num-layers", type=int, default=16)
    t.add_argument("--rank", type=int, default=16)
    t.add_argument("--scale", type=float, default=20.0)
    t.add_argument("--learning-rate", type=float, default=2e-5)
    t.add_argument("--temp", type=float, default=2.0)
    t.set_defaults(func=train)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
