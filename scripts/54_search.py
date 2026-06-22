#!/usr/bin/env python3
"""③ Search, not sample — verifier-guided beam search over solutions. Instead of one
linear repair chain (50), maintain a BEAM of solution lineages; at each depth expand
every member, COMPILE+RUN each child, and keep the top-K by real-verifier score
(passed > fewer-errors). The compiler/tests are the value function; branches that
don't compile are pruned. Free local compute lets us explore beam×children×depth
branches per task — a metered cloud model can't afford the search. Best for the hard
tasks where the first chain stalls.

  python scripts/54_search.py --base-url http://localhost:8080/v1 --lang rust \
      --task "lru_cache with O(1) get/put" --harness "..." --beam 3 --depth 4
  python scripts/54_search.py --selftest      # GPU-free
"""
import argparse
import importlib.util
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from verifiers import verify  # noqa: E402

_spec = importlib.util.spec_from_file_location("agentic", os.path.join(HERE, "50_agentic_loop.py"))
agentic = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(agentic)


def _key(rc):
    """Value function: passing beats failing; among fails, fewer-error (shorter diag)."""
    r = rc[0]
    return (not r.passed, len(r.diag))


def beam_search(propose, lang, task, harness, *, beam=3, depth=4, children=2, log=print):
    """Returns (solution_or_best, trace). Explores up to beam*children*depth branches."""
    trace = {"task": task, "lang": lang, "branches": 0, "solved": False, "depth": 0}
    # seed the beam with diverse first attempts
    frontier = []
    for i in range(beam):
        code = propose(task, lang, "", "", 0.2 + 0.25 * i)
        r = verify(lang, code, harness)
        trace["branches"] += 1
        if r.passed and r.stage != "skip":                       # a no-toolchain SKIP is neutral, NOT a solve
            trace.update(solved=True, depth=0, solution=code)
            log(f"  depth 0: solved on seed {i}")
            return code, trace
        frontier.append((r, code))
    for d in range(1, depth + 1):
        cands = []
        for r, code in frontier:
            for j in range(children):
                child = propose(task, lang, f"[{r.stage}] {r.diag}", code, 0.15 + 0.3 * j)
                cr = verify(lang, child, harness)
                trace["branches"] += 1
                if cr.passed and cr.stage != "skip":             # SKIP ≠ solved
                    trace.update(solved=True, depth=d, solution=child)
                    log(f"  depth {d}: SOLVED ({trace['branches']} branches explored)")
                    return child, trace
                cands.append((cr, child))
        frontier = sorted(cands, key=_key)[:beam]               # beam prune by verifier
        best = frontier[0][0]
        log(f"  depth {d}: beam kept {len(frontier)}; best still failing at "
            f"[{best.stage}] ({len(best.diag)} diag chars)")
    trace["depth"] = depth
    trace["solution"] = frontier[0][1]
    return frontier[0][1], trace


def selftest():
    """GPU-free: a stub where only the SECOND child of a repair is correct — a linear
    chain that always took child-0 would miss it; beam search explores both and finds it."""
    task = "clamp(x,lo,hi)"
    harness = "assert clamp(5,0,3)==3 and clamp(-1,0,3)==0 and clamp(2,0,3)==2"
    st = {"n": 0}

    def propose(t, lang, diag, prev, temp):
        st["n"] += 1
        if not diag:
            return "def clamp(x,lo,hi): return x"                       # wrong seed
        # child-0 (low temp) stays wrong; a higher-temp child gets it right
        if temp >= 0.4:
            return "def clamp(x,lo,hi): return max(lo, min(x, hi))"     # correct
        return "def clamp(x,lo,hi): return min(x, hi)"                  # still wrong

    sol, trace = beam_search(propose, "python", task, harness, beam=2, depth=3, children=2)
    ok = trace["solved"] and verify("python", sol, harness).passed
    print(f"  selftest: solved={trace['solved']} after exploring {trace['branches']} "
          f"branches (beam found the higher-temp correct child)  {'PASS ✅' if ok else 'FAIL'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--lang", default="python")
    ap.add_argument("--task", default="")
    ap.add_argument("--harness", default="")
    ap.add_argument("--beam", type=int, default=3)
    ap.add_argument("--depth", type=int, default=4)
    args = ap.parse_args()
    if args.selftest:
        raise SystemExit(0 if selftest() else 1)
    propose = agentic.make_proposer(args.base_url, args.model)
    sol, trace = beam_search(propose, args.lang, args.task, args.harness,
                             beam=args.beam, depth=args.depth)
    print(f"\n  {'✅ SOLVED' if trace['solved'] else '⚠️ best-effort'} "
          f"({trace['branches']} branches, depth {trace['depth']})")
    if sol:
        print("\n" + sol)


if __name__ == "__main__":
    main()
