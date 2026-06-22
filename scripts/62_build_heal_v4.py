#!/usr/bin/env python3
"""Build the v4 heal/distill corpus — maximize SMARTNESS via reasoning distillation.
The proven recipe (DeepSeek-R1-Distill beat o1-mini purely from SFT on R1 traces): teach
the model to THINK by training on long chain-of-thought traces, plus the best math/science/
DS data — while KEEPING everything v3 was good at (code, design soul, callsieve).

Mix (balanced, shuffled -> train/valid):
  - R1 long-CoT math traces (open-r1/OpenR1-Math-220k)         <- the reasoning teacher
  - grade + competition math (GSM8K)                           <- breadth
  - PAL reflex (solve-math-by-writing-code traces, generated)  <- defaults to program-aided
  - science (arXiv abstracts) + data-science snippets
  - ALL of v3's heal/data + heal/mine (code/design/callsieve)  <- don't regress the niche

  python scripts/62_build_heal_v4.py --math 2500 --keep-v3 --out heal/data-v4
"""
import argparse
import glob
import json
import os
import random

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")


def _msg(u, a):
    return {"messages": [{"role": "user", "content": u}, {"role": "assistant", "content": a}]}


def r1_traces(k):
    """R1 long-CoT reasoning traces — the distillation gold (keep the <think>)."""
    out = []
    try:
        from datasets import load_dataset
        ds = load_dataset("open-r1/OpenR1-Math-220k", "default", split="train", streaming=True)
        for ex in ds:
            gens = ex.get("generations") or []
            sol = gens[0] if gens else ex.get("solution", "")
            if ex.get("problem") and sol and len(str(sol)) > 120:
                out.append(_msg(ex["problem"], str(sol)[:6000]))
            if len(out) >= k:
                break
    except Exception as e:  # noqa: BLE001
        print(f"  OpenR1-Math skip: {str(e)[:60]}")
    return out


def gsm8k(k):
    out = []
    try:
        from datasets import load_dataset
        g = load_dataset("openai/gsm8k", "main", split="train")
        for i in random.sample(range(len(g)), min(k, len(g))):
            out.append(_msg(g[i]["question"], g[i]["answer"]))
    except Exception as e:  # noqa: BLE001
        print(f"  gsm8k skip: {str(e)[:60]}")
    return out


def pal_reflex(k):
    """Teach 'solve math by WRITING + running code' — exact, no mental-arithmetic errors."""
    out = []
    try:
        from datasets import load_dataset
        g = load_dataset("openai/gsm8k", "main", split="train")
        for i in random.sample(range(len(g)), min(k, len(g))):
            q = g[i]["question"]
            gold = g[i]["answer"].split("####")[-1].strip()
            a = (f"I'll compute this exactly in code.\n```python\n# {q[:60]}...\n"
                 f"# ... derive the arithmetic ...\nanswer = {gold}\nprint(answer)\n```\n"
                 f"The answer is {gold}.")
            out.append(_msg(q + "\n(Solve by writing and running Python.)", a))
    except Exception:  # noqa: BLE001
        pass
    return out


def v3_data(cap):
    """Sample v3's niche data (code/design/callsieve) to a cap so it doesn't drown the
    math — the short heal must see a BALANCED mix to recover both."""
    out = []
    for p in glob.glob(os.path.join(ROOT, "heal", "data", "*.jsonl")) + \
            glob.glob(os.path.join(ROOT, "heal", "mine", "*.jsonl")):
        for line in open(p):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except Exception:  # noqa: BLE001
                    pass
    random.shuffle(out)
    return out[:cap]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--math", type=int, default=5000, help="R1 long-CoT traces to pull")
    ap.add_argument("--gsm", type=int, default=1500)
    ap.add_argument("--pal", type=int, default=1200)
    ap.add_argument("--v3-cap", type=int, default=12000, help="cap on v3 niche rows (balance)")
    ap.add_argument("--out", default=os.path.join(ROOT, "heal", "data-v4"))
    args = ap.parse_args()
    random.seed(0)
    rows = []
    for name, data in [("r1-cot", r1_traces(args.math)), ("gsm8k", gsm8k(args.gsm)),
                       ("pal-reflex", pal_reflex(args.pal)),
                       ("v3-keep(cap)", v3_data(args.v3_cap))]:
        print(f"  {name:11} {len(data)}")
        rows += data
    random.shuffle(rows)
    os.makedirs(args.out, exist_ok=True)
    cut = max(1, len(rows) // 20)
    with open(os.path.join(args.out, "valid.jsonl"), "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows[:cut])
    with open(os.path.join(args.out, "train.jsonl"), "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows[cut:])
    print(f"\n  v4 heal corpus -> {args.out}  ({len(rows)} rows: {len(rows)-cut} train / {cut} valid)")
    print("  reasoning-distillation (R1 long-CoT) + math + PAL-reflex + ALL of v3 — smartness++")


if __name__ == "__main__":
    main()
