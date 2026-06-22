#!/usr/bin/env python3
"""Benchmark runner — a NUMBER on a recognized benchmark. Runs the SERVED model on
HumanEval (pass@1, single-shot, scored on the HIDDEN test via src/verifiers) — directly
comparable to published frontier/open results. `--loop` wraps our agentic verify-repair
(scripts/50) so we can see the verification LIFT over raw pass@1.

  python scripts/58_bench.py --n 20                 # raw pass@1
  python scripts/58_bench.py --n 20 --loop          # + agentic verify-repair
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from verifiers import verify  # noqa: E402


def chat(base_url, prompt, model, max_tokens=1000):
    import time as _t
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.0, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    for attempt in range(4):                             # retry transient server hiccups (don't crash the bench)
        try:
            req = urllib.request.Request(base_url + "/chat/completions", body, {"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]["content"]
        except Exception:  # noqa: BLE001
            if attempt == 3:
                raise
            _t.sleep(2 * (attempt + 1))


def _extract(text):
    m = re.findall(r"```[a-zA-Z0-9]*\n(.*?)```", text, re.S)
    return (m[-1] if m else text).strip()


def score(solution, test, entry_point):
    """HumanEval hidden-test score: define the fn + the check, run check(entry_point)."""
    code = f"{solution}\n\n{test}\n\ncheck({entry_point})\n"
    return verify("python", code, "").passed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--loop", action="store_true")
    args = ap.parse_args()
    from datasets import load_dataset
    ds = load_dataset("openai/openai_humaneval", split="test")
    loop = None
    if args.loop:
        spec = importlib.util.spec_from_file_location("ag", os.path.join(HERE, "50_agentic_loop.py"))
        loop = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loop)

    npass = 0
    actual = min(args.n, len(ds))                        # the real # scored (HumanEval=164); args.n may exceed it
    for i in range(actual):
        p = ds[i]
        if loop:  # iterate against the docstring's own examples, score on hidden test
            pub = "\n".join(f"assert {ln}" for ln in _doctests(p["prompt"], p["entry_point"]))
            prop = loop.make_proposer(args.base_url, args.model)
            sol = loop.agentic_solve(prop, "python", "Complete:\n" + p["prompt"], pub,
                                     budget=4, branch=1, log=lambda *a: None)[0] or ""
        else:
            sol = _extract(chat(args.base_url, "Complete this Python function. Output ONLY the "
                                "complete function in one code block:\n\n" + p["prompt"], args.model))
        ok = score(sol, p["test"], p["entry_point"])
        npass += ok
        print(f"    {p['task_id']}: {'✓' if ok else '✗'}", flush=True)
    mode = "agentic-loop" if args.loop else "single-shot"
    print(f"\n  HumanEval pass@1 ({mode}): {npass}/{actual}  ({100*npass//max(actual,1)}%)"
          "  [hidden-test scored, comparable to published]")


def _doctests(prompt, entry):
    """Best-effort: pull '>>> entry(args) -> result' example pairs from the docstring."""
    out = []
    lines = prompt.splitlines()
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith(">>>") and entry in s and i + 1 < len(lines):
            call = s[3:].strip()
            res = lines[i + 1].strip()
            if res and not res.startswith(">>>"):
                out.append(f"{call} == {res}")
    return out[:4]


if __name__ == "__main__":
    main()
