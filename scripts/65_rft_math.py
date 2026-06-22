#!/usr/bin/env python3
"""Verified math RFT (STaR) — the math model teaches ITSELF. Generate N solutions per GSM8K
problem, KEEP ONLY the ones whose final answer is VERIFIED-correct (exact match to the gold
answer), and SFT on those. Self-distillation from the VERIFIER (ground truth), not a weak
teacher — the thesis applied to math. Generates on the TRAIN split; eval (59) is on TEST, so
there's no contamination. Mixes in a sample of the general heal data to avoid forgetting code.

  # serve v4 on :8080 first (ideally + the speculative draft for speed), then:
  python scripts/65_rft_math.py gen --n 60 --attempts 3
  python scripts/06_heal_lora.py --model models/GLM-5.2-q3a4-v4 --mode sft --skip-data \
      --data heal/rft-math --adapter-path heal/adapters-v4-rft --no-mask-prompt --num-layers 6 --iters 500
"""
import argparse
import importlib.util
import json
import os
import random
import re
import sys

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "heal", "rft-math")
HEAL = os.path.join(HERE, "..", "heal", "data-v4", "train.jsonl")

# reuse 59_stem_diag.chat() (the served-model API helper)
_spec = importlib.util.spec_from_file_location("diag", os.path.join(HERE, "59_stem_diag.py"))
diag = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(diag)


def final_num(text):
    """Extract the model's final numeric answer ('The answer is X.' preferred, else last number)."""
    m = re.findall(r"answer is[^\d\-]*(-?[\d,]+(?:\.\d+)?)", text or "", re.I)
    if m:
        return m[-1].replace(",", "").rstrip(".")
    nums = re.findall(r"-?[\d,]+(?:\.\d+)?", text or "")
    return nums[-1].replace(",", "").rstrip(".") if nums else None


def gen(base_url, model, n, attempts):
    from datasets import load_dataset
    ds = load_dataset("openai/gsm8k", "main", split="train")     # TRAIN — eval is on TEST
    rows, solved = [], 0
    for i in range(n):
        q = ds[i]["question"]
        gold = ds[i]["answer"].split("####")[-1].strip().replace(",", "")
        prompt = q + "\n\nReason step by step, then end with 'The answer is <number>.'"
        for _ in range(attempts):
            out = diag.chat(base_url, prompt, model, think=True, max_tokens=900)
            if final_num(out) == gold:                            # VERIFIED correct
                rows.append({"messages": [{"role": "user", "content": prompt},
                                          {"role": "assistant", "content": out.strip()}]})
                solved += 1
                break                                             # one correct trace per problem (STaR)
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{n} problems · {solved} solved · {len(rows)} verified traces", flush=True)
    # anti-forgetting: mix in ~30% general heal data
    mix = []
    if os.path.exists(HEAL):
        heal = [l for l in open(HEAL) if l.strip()]
        random.seed(0)
        mix = [json.loads(l) for l in random.sample(heal, min(len(heal), max(20, len(rows) // 2)))]
    allrows = rows + mix
    random.shuffle(allrows)
    os.makedirs(OUT, exist_ok=True)
    nv = max(2, len(allrows) // 20)
    open(os.path.join(OUT, "valid.jsonl"), "w").write("\n".join(json.dumps(r) for r in allrows[:nv]))
    open(os.path.join(OUT, "train.jsonl"), "w").write("\n".join(json.dumps(r) for r in allrows[nv:]))
    rate = round(100 * solved / max(1, n))
    print(f"  RFT: {solved}/{n} GSM8K solved ({rate}%) -> {len(rows)} verified-correct traces "
          f"+ {len(mix)} heal -> {OUT}")
    if solved < max(3, n // 10):
        print("  ⚠️ COLD START: very few correct traces — the base is too weak at math for RFT to help. "
              "Skip RFT; the SFT-R1 adapter stands.")
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    g.add_argument("--model", default="glm")
    g.add_argument("--n", type=int, default=60)
    g.add_argument("--attempts", type=int, default=3)
    args = ap.parse_args()
    gen(args.base_url, args.model, args.n, args.attempts)


if __name__ == "__main__":
    main()
