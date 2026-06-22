#!/usr/bin/env python3
"""STEM diagnostic — how much did pruning + coding-focused heal cost MATH/SCIENCE? Runs
grade-school math (GSM8K) + a small algebra set through the SERVED model and scores it,
so we know the RAW capability gap BEFORE any STEM heal. Raw single-shot (thinking ON) is
the honest measure of the model itself; the sympy/repl tools lift it afterward. Re-run
after the heal to measure the lift.

  python scripts/59_stem_diag.py --n 15 --base-url http://localhost:8080/v1
"""
import argparse
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(__file__)


def chat(base_url, prompt, model, think=True, max_tokens=8192):
    import time as _t
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.0, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": think}}).encode()
    for attempt in range(4):                             # retry transient server hiccups (don't crash the diag)
        try:
            req = urllib.request.Request(base_url + "/chat/completions", body, {"Content-Type": "application/json"})
            msg = json.loads(urllib.request.urlopen(req, timeout=900).read())["choices"][0]["message"]
            return msg.get("content") or msg.get("reasoning") or msg.get("reasoning_content") or ""
        except Exception:  # noqa: BLE001
            if attempt == 3:
                raise
            _t.sleep(2 * (attempt + 1))


def _last_number(text):
    nums = re.findall(r"-?\d[\d,]*\.?\d*", (text or "").replace(",", ""))
    return nums[-1] if nums else None


def gsm8k(base_url, model, n):
    try:
        from datasets import load_dataset
        ds = load_dataset("openai/gsm8k", "main", split="test")
    except Exception as e:  # noqa: BLE001
        print(f"  GSM8K load failed ({str(e)[:60]}) — skipping")
        return None
    npass = 0
    for i in range(n):
        q, gold = ds[i]["question"], re.sub(r"[^0-9.\-]", "", ds[i]["answer"].split("####")[-1])  # strip $/,/spaces → float-safe
        out = chat(base_url, q + "\n\nReason step by step, then end with 'The answer is <number>.'", model)
        pred = _last_number(out)
        try:
            ok = pred is not None and abs(float(pred) - float(gold)) < 1e-3
        except ValueError:
            ok = False
        npass += ok
        print(f"    q{i+1}: pred={pred} gold={gold} {'✓' if ok else '✗'}", flush=True)
    return npass, n


# A few algebra/calculus problems with SymPy-checkable answers (no dataset needed).
ALGEBRA = [
    ("Expand (x+3)(x-5). Give only the polynomial.", "x**2-2*x-15"),
    ("Differentiate x**3 + 2*x with respect to x. Answer only.", "3*x**2+2"),
    ("Solve 2*x + 6 = 0 for x. Answer only the number.", "-3"),
    ("Simplify (x**2-1)/(x-1). Answer only.", "x+1"),
]


def algebra(base_url, model):
    import sympy
    from sympy.parsing.sympy_parser import parse_expr
    npass = 0
    for q, gold in ALGEBRA:
        out = chat(base_url, q, model)
        m = re.findall(r"[-0-9x+*/(). ^]+", out.replace("**", "^"))
        cand = max(m, key=len).strip().replace("^", "**") if m else ""
        try:
            ok = sympy.simplify(parse_expr(cand) - parse_expr(gold)) == 0
        except Exception:  # noqa: BLE001
            ok = False
        npass += ok
        print(f"    {q[:38]}... -> {'✓' if ok else '✗'} (got {cand[:24]!r})", flush=True)
    return npass, len(ALGEBRA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--n", type=int, default=12)
    args = ap.parse_args()
    print("  STEM diagnostic — RAW model capability (thinking ON, no tools)\n")
    print("  [GSM8K grade-school math]")
    g = gsm8k(args.base_url, args.model, args.n)
    print("\n  [algebra/calculus, SymPy-checked]")
    a = algebra(args.base_url, args.model)
    print("\n  === DIAGNOSIS ===")
    if g:
        print(f"  GSM8K: {g[0]}/{g[1]}  ({100*g[0]//g[1]}%)")
    print(f"  Algebra: {a[0]}/{a[1]}  ({100*a[0]//max(a[1],1)}%)")
    print("  (raw single-shot; sympy/repl verifiers + a STEM heal lift this — the gap to close)")


if __name__ == "__main__":
    main()
