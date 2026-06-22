#!/usr/bin/env python3
"""④ Local multi-agent team (free, on-device). A CODER (the agentic loop, 50) writes
a solution that passes the given tests; an ADVERSARIAL TESTER then writes edge-case
tests trying to BREAK it; anything that breaks is fed back to the coder to fix. Net:
the solution is hardened against cases the original tests missed — adversarial
self-play raises correctness with zero API cost. The whole team runs in the loop on
your machine; a metered cloud model can't afford this many rounds.

  python scripts/51_multi_agent.py --base-url http://localhost:8080/v1 --lang python \
      --task "parse_int(s): parse a base-10 int, raise ValueError on junk" \
      --harness "assert parse_int('42')==42" --rounds 2
  python scripts/51_multi_agent.py --selftest      # GPU-free
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

_spec = importlib.util.spec_from_file_location("agentic", os.path.join(HERE, "50_agentic_loop.py"))
agentic = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(agentic)


def gen_adversarial(base_url, model, lang, task, solution, n=4):
    """The adversarial tester: edge-case assertions that try to break the solution."""
    sysmsg = ("You are a ruthless test engineer. Output ONLY a fenced code block of "
              f"{n} {lang} assertions targeting edge cases (empty, boundary, negative, "
              "unicode, overflow, malformed) that might BREAK the given solution. "
              "Assertions only — assume the solution's symbols are in scope.")
    user = f"Task: {task}\n\nSolution under test:\n```{lang}\n{solution}\n```\n\nEdge-case assertions:"
    body = json.dumps({"model": model, "temperature": 0.6, "max_tokens": 700,
                       "messages": [{"role": "system", "content": sysmsg},
                                    {"role": "user", "content": user}],
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(base_url + "/chat/completions", body,
                                 {"Content-Type": "application/json"})
    txt = json.loads(urllib.request.urlopen(req, timeout=200).read())["choices"][0]["message"]["content"]
    m = re.findall(r"```[a-zA-Z0-9]*\n(.*?)```", txt, re.S)
    return (m[-1] if m else txt).strip()


def team_solve(coder, adv_gen, lang, task, harness, *, budget=8, rounds=2, log=print):
    """coder solves -> adversarial tester attacks -> coder repairs against the harder
    harness. Returns (solution, hardened_harness, trace)."""
    full = harness
    sol, trace = agentic.agentic_solve(coder, lang, task, full, budget=budget, branch=2, log=log)
    trace["adversarial_rounds"] = 0
    for rnd in range(rounds):
        if not sol:
            break
        adv = adv_gen(lang, task, sol)
        if not adv.strip():
            break
        r = verify(lang, sol, full + "\n" + adv)
        log(f"  [adversarial round {rnd}] new tests -> {'SURVIVED ✅' if r.passed else 'BROKE IT, repairing…'}")
        full = full + "\n" + adv
        trace["adversarial_rounds"] = rnd + 1
        if r.passed:
            break                                       # robust against the attack
        sol, t2 = agentic.agentic_solve(coder, lang, task, full, budget=budget, branch=2, log=log)
        trace["attempts"] += t2["attempts"]
        trace["solved"] = t2["solved"]
    return sol, full, trace


def selftest():
    """GPU-free. Stub coder first ships parse that ignores the empty-string edge case;
    the stub adversarial tester surfaces it; the coder then handles it -> hardened."""
    task = "first_or_zero(xs): return xs[0], or 0 if empty"
    harness = "assert first_or_zero([7,8])==7"
    st = {"saw_adv": False}

    def coder(task, lang, diag, prev, temp):
        if st["saw_adv"] or "IndexError" in diag or "empty" in diag.lower():
            return "def first_or_zero(xs):\n    return xs[0] if xs else 0"
        return "def first_or_zero(xs):\n    return xs[0]"          # ignores empty

    def adv_gen(lang, task, solution):
        st["saw_adv"] = True
        return "assert first_or_zero([])==0"                       # the edge case

    sol, full, trace = team_solve(coder, adv_gen, "python", task, harness, budget=4, rounds=2)
    final_ok = verify("python", sol, full).passed
    ok = final_ok and trace["adversarial_rounds"] >= 1
    print(f"  selftest: hardened over {trace['adversarial_rounds']} adversarial round(s); "
          f"final passes augmented tests={final_ok}  {'PASS ✅' if ok else 'FAIL'}")
    print(f"  final solution: {sol!r}")
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
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--trace-out", default="")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(0 if selftest() else 1)
    coder = agentic.make_proposer(args.base_url, args.model)
    sol, full, trace = team_solve(
        coder, lambda l, t, s: gen_adversarial(args.base_url, args.model, l, t, s),
        args.lang, args.task, args.harness, budget=args.budget, rounds=args.rounds)
    print(f"\n  {'✅ SOLVED + HARDENED' if trace.get('solved') else '⚠️ best-effort'} "
          f"({trace.get('adversarial_rounds',0)} adversarial rounds)")
    if sol:
        print("\n" + sol)
    if args.trace_out:
        with open(args.trace_out, "a") as f:
            f.write(json.dumps(trace) + "\n")


if __name__ == "__main__":
    main()
