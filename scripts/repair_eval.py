"""Repair-eval gate (#16) — does the repair-healed model actually FIX buggy code? Loads v4 + adapters-repair,
takes held-out (good, bad) repair examples, asks the model to fix each bad one, and verify_many checks the
output. Reports the pass-rate — the honest "did closing the loop work" number.

  python scripts/repair_eval.py --adapter heal/adapters-repair --eval heal/_q_repair/eval.jsonl
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default="heal/adapters-repair")
    ap.add_argument("--eval", default="heal/_q_repair/eval.jsonl")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v4")
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    from mlx_lm import load, generate
    from verifiers import verify
    model, tok = load(a.model, adapter_path=a.adapter)
    rows = [json.loads(line) for line in open(a.eval) if line.strip()][:a.n]
    passed = baseline = 0
    for r in rows:
        msgs = r["messages"][:2]                                       # system + the buggy-code user turn
        prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        out = generate(model, tok, prompt=prompt, max_tokens=400, verbose=False)
        m = re.search(r"```(?:python)?\n(.*?)```", out, re.S)
        code = m.group(1) if m else out
        res = verify("python", code, "")
        if res and res.passed:
            passed += 1
        # baseline: did the buggy code already fail? (sanity — it should)
        bad = re.search(r"```(?:python)?\n(.*?)```", msgs[1]["content"], re.S)
        if bad:
            rb = verify("python", bad.group(1), "")
            baseline += 1 if (rb and rb.passed) else 0
    n = len(rows)
    print(f"  repair-eval: model fixed {passed}/{n} ({100*passed/max(1,n):.0f}%) · "
          f"buggy-inputs that already passed: {baseline}/{n} (should be ~0) · adapter={a.adapter}")


if __name__ == "__main__":
    main()
