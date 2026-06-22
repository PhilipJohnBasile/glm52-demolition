#!/usr/bin/env python3
"""① Deep agentic loop — the frontier-killer engine. plan -> write -> RUN tests ->
read the REAL error -> repair -> (when green) refactor, with a compute BUDGET and
best-of-N branching. Free local verification beats a metered cloud model on hard
tasks: we just keep iterating until the real test passes. Verifies via
src/verifiers (real compile+execute). Emits a structured trace the flywheel (52)
harvests, and is the unit the multi-agent team (51) drives.

  python scripts/50_agentic_loop.py --lang python --base-url http://localhost:8080/v1 \
      --model models/GLM-5.2-q3a4-v2 --budget 8 --branch 2 \
      --task "is_palindrome(s): ignore case and non-alphanumerics" \
      --harness "assert is_palindrome('A man, a plan, a canal: Panama') and not is_palindrome('abc')"
  python scripts/50_agentic_loop.py --selftest        # GPU-free logic check
"""
import argparse
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from verifiers import verify  # noqa: E402

SYS = "You are an expert engineer. Output ONLY one fenced code block — no prose, no explanation."


def _extract(text):
    m = re.findall(r"```[a-zA-Z0-9]*\n(.*?)```", text, re.S)
    return (m[-1] if m else text).strip()


def make_proposer(base_url, model):
    """Real proposer: ask the served model for code (initial or repair)."""
    def propose(task, lang, diag, prev, temp):
        if diag:
            user = (f"Task ({lang}): {task}\n\nYour previous attempt:\n```{lang}\n{prev}\n```\n\n"
                    f"It FAILED with this REAL output:\n{diag}\n\nFix the root cause. Full corrected code only.")
        else:
            user = f"Task ({lang}): {task}\n\nWrite a correct, idiomatic solution. Code only."
        body = json.dumps({"model": model, "temperature": temp, "max_tokens": 1400,
                           "messages": [{"role": "system", "content": SYS},
                                        {"role": "user", "content": user}],
                           "chat_template_kwargs": {"enable_thinking": False}}).encode()
        req = urllib.request.Request(base_url + "/chat/completions", body,
                                     {"Content-Type": "application/json"})
        txt = json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]["content"]
        return _extract(txt)
    return propose


def agentic_solve(propose, lang, task, harness, *, budget=8, branch=2, log=print):
    """Iterate write->verify->repair until green or budget spent, then refactor.
    Returns (solution_or_None, trace). best-of-N branching per iteration; free local
    compute = high budget = the asymmetry over a metered cloud model."""
    trace = {"task": task, "lang": lang, "attempts": [], "solved": False, "iters": 0}
    diag, prev, solved = "", "", None
    for it in range(budget):
        cands = []
        for b in range(branch):
            temp = 0.0 if (it == 0 and b == 0) else 0.4 + 0.15 * b
            code = propose(task, lang, diag, prev, temp)
            r = verify(lang, code, harness)
            cands.append((r, code))
            if r.passed:
                break
        # prefer a passing candidate; else the one closest to passing (shortest diag)
        r, code = sorted(cands, key=lambda rc: (not rc[0].passed, len(rc[0].diag)))[0]
        trace["attempts"].append({"iter": it, "stage": r.stage, "passed": r.passed,
                                  "diag": r.diag[:200]})
        trace["iters"] = it + 1
        log(f"  iter {it}: stage={r.stage:8} passed={r.passed}"
            + ("" if r.passed else f"   ↳ {r.diag.splitlines()[-1][:80] if r.diag else ''}"))
        if r.passed:
            solved, trace["solved"] = code, True
            break
        prev, diag = code, f"[{r.stage}] {r.diag}"

    if solved:                                          # refactor pass — improve, stay green
        ref = propose(task + " — refactor for clarity/idiom; keep behavior identical",
                      lang, "", solved, 0.2)
        if verify(lang, ref, harness).passed:
            solved = ref
            trace["refactored"] = True
    trace["solution"] = solved                          # carried for the flywheel (52)
    trace["harness"] = harness
    return solved, trace


def selftest():
    """GPU-free: a stub proposer that emits a buggy solution first, then the correct
    one after seeing the real AssertionError — proving the loop reads diagnostics and
    converges. Mirrors how the real model behaves with the verifier in the loop."""
    task = "add(a,b) returns a+b"
    harness = "assert add(2,3)==5 and add(-1,1)==0"
    state = {"n": 0}

    def stub(task, lang, diag, prev, temp):
        state["n"] += 1
        if not diag:
            return "def add(a,b):\n    return a-b"          # wrong on first write
        return "def add(a,b):\n    return a+b"              # fixed after seeing the failure

    sol, trace = agentic_solve(stub, "python", task, harness, budget=4, branch=1)
    ok = sol is not None and trace["solved"] and trace["iters"] == 2
    print(f"  selftest: solved={trace['solved']} in {trace['iters']} iters "
          f"(buggy->repair->green)  {'PASS ✅' if ok else 'FAIL'}")
    print(f"  final solution:\n    {sol.replace(chr(10), chr(10)+'    ')}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--lang", default="python")
    ap.add_argument("--task", default="")
    ap.add_argument("--harness", default="")
    ap.add_argument("--budget", type=int, default=8)
    ap.add_argument("--branch", type=int, default=2)
    ap.add_argument("--trace-out", default="")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(0 if selftest() else 1)
    propose = make_proposer(args.base_url, args.model)
    sol, trace = agentic_solve(propose, args.lang, args.task, args.harness,
                               budget=args.budget, branch=args.branch)
    print(f"\n  {'✅ SOLVED' if trace['solved'] else '⚠️ best-effort'} in {trace['iters']} iters")
    if sol:
        print("\n" + sol)
    if args.trace_out:
        with open(args.trace_out, "a") as f:
            f.write(json.dumps(trace) + "\n")


if __name__ == "__main__":
    main()
