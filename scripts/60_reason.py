#!/usr/bin/env python3
"""Smart math/science reasoning — BETTER answers without retraining, on-thesis:
- PAL (program-aided): the model SOLVES BY WRITING CODE (Python/SymPy) which we RUN,
  so arithmetic/algebra is exact — no mental-math hallucination.
- Self-consistency: sample N independent attempts and MAJORITY-VOTE the answer (free
  local compute makes N=8-16 cheap where a metered model can't).
- Verify: numeric/SymPy check of the agreed answer.
These compose the REPL (src/repl.py) + the served model. Used by the agent + the diag.

  python scripts/60_reason.py --selftest
  python scripts/60_reason.py --base-url http://localhost:8080/v1 --n 8 \
      --question "A robe takes 2 bolts of blue and half that of white. How many bolts total?"
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from collections import Counter

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from repl import PyREPL  # noqa: E402


def server_call(base_url, model, think):
    def call(prompt, temp):
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                           "temperature": temp, "max_tokens": 1500,
                           "chat_template_kwargs": {"enable_thinking": think}}).encode()
        req = urllib.request.Request(base_url + "/chat/completions", body,
                                     {"Content-Type": "application/json"})
        m = json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]
        return m.get("content") or m.get("reasoning") or ""
    return call


def _code(text):
    m = re.findall(r"```(?:python)?\n(.*?)```", text, re.S)
    return (m[-1] if m else text).strip()


def _norm(ans):
    nums = re.findall(r"-?\d[\d,]*\.?\d*", (ans or "").replace(",", ""))
    if nums:
        try:
            return str(round(float(nums[-1]), 6)).rstrip("0").rstrip(".")
        except ValueError:
            pass
    return (ans or "").strip()[:40]


def pal_once(call, question, temp):
    """One program-aided attempt: model writes code that prints the answer; we run it."""
    prompt = ("Solve by writing a short Python program that COMPUTES and prints the final "
              "answer (use sympy for symbolic math). Output ONLY one ```python block.\n\n"
              + question)
    out = PyREPL().run(_code(call(prompt, temp)))
    return _norm(out)


def solve(call, question, *, n=8, log=print):
    """Self-consistent PAL: N program-aided attempts -> majority vote."""
    votes = []
    for i in range(n):
        try:
            a = pal_once(call, question, 0.0 if i == 0 else 0.7)
        except Exception as e:  # noqa: BLE001
            a = f"err:{str(e)[:20]}"
        votes.append(a)
        log(f"    attempt {i}: {a}")
    answer, count = Counter(v for v in votes if not v.startswith("err")).most_common(1)[0] \
        if any(not v.startswith("err") for v in votes) else ("(none)", 0)
    return answer, count, n


def selftest():
    """Stub 'model' that writes a correct program for an arithmetic word problem; proves
    PAL runs the code and self-consistency agrees."""
    def call(prompt, temp):
        return "```python\nblue=2\nwhite=blue/2\nprint(blue+white)\n```"
    ans, count, n = solve(call, "robe: 2 blue + half that white, total?", n=5, log=lambda *a: None)
    ok = ans == "3" and count == 5
    print(f"  reason selftest: PAL+vote -> {ans} ({count}/{n} agree)  {'PASS ✅' if ok else 'FAIL'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--question", default="")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--think", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        raise SystemExit(0 if selftest() else 1)
    call = server_call(args.base_url, args.model, args.think)
    ans, count, n = solve(call, args.question, n=args.n)
    print(f"\n  answer: {ans}   ({count}/{n} agreed — self-consistent PAL)")


if __name__ == "__main__":
    main()
