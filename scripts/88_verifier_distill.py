#!/usr/bin/env python3
"""Verifier-guided distillation — recover capability HONESTLY (the novel lever from the strategy chat).

A TEACHER (the original full GLM-5.2 streamed, or a frontier model via API) solves hard problems → OUR verifier mesh
CHECKS each solution → keep ONLY the machine-verified-correct → SFT the student on them. Every training example
passed a real compiler / test / proof, so: no contamination, no hallucinated "solutions" — the student learns only
from solutions that actually work. Fits the verify-everything spine and recovers what the 3-bit demolition lost.

CPU here: the harness + the verify-FILTER (selftested). GPU at run: the teacher generation + the SFT (06_heal_lora).
Critically REQUIRES a real pass (stage != 'skip') — a skip means "no toolchain to judge" = neutral, NOT a pass;
counting skips would re-introduce the false-PASS bug we fixed this session.

  python scripts/88_verifier_distill.py --selftest    # CPU: prove the filter keeps ONLY verified-correct
"""
import argparse
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))


def is_verified(domain, solution, harness="", setup=""):
    """OUR mesh judges the teacher's solution. True only on a REAL pass (skip = no toolchain = neutral, not a pass)."""
    from verifiers import verify, verify_sql, verify_lean, verify_domain
    d = (domain or "").lower()
    if d in ("python", "py", "rust", "rs", "go", "golang"):
        r = verify(d, solution, harness)
    elif d == "sql":
        r = verify_sql(solution, setup)
    elif d in ("lean", "math", "proof"):
        r = verify_lean(solution)
    else:
        r = verify_domain(domain, solution, harness=harness, setup=setup)
    return bool(r.passed) and r.stage != "skip"


def distill(domain, teacher_fn, problems):                 # GPU at run (teacher_fn calls a model)
    """teacher solves → verify → keep only verified-correct. Returns (SFT-ready chat records, n_tried)."""
    kept, tried = [], 0
    for p in problems:
        tried += 1
        sol = teacher_fn(p["problem"])
        if is_verified(domain, sol, p.get("harness", ""), p.get("setup", "")):
            kept.append({"messages": [{"role": "user", "content": p["problem"]},
                                      {"role": "assistant", "content": sol}]})
    return kept, tried


def _selftest():
    prob = {"problem": "Write add(a,b).", "harness": "assert add(2,3)==5 and add(-1,1)==0"}
    good = "def add(a, b):\n    return a + b"
    bad = "def add(a, b):\n    return a - b"
    assert is_verified("python", good, prob["harness"]), "FILTER REJECTED a correct solution"
    assert not is_verified("python", bad, prob["harness"]), "FILTER ACCEPTED a wrong solution"
    kept, tried = distill("python", lambda q: good, [prob, prob])
    assert len(kept) == 2 and tried == 2, "good teacher: should keep all"
    kept_bad, _ = distill("python", lambda q: bad, [prob])
    assert len(kept_bad) == 0, "kept an UNVERIFIED solution — filter broken"
    print(f"  verifier_distill selftest PASS — keeps ONLY machine-verified ({len(kept)}/2 good kept, 0/1 bad kept)")
    print("  → GPU: teacher (orig GLM-5.2 / frontier) solves hard problems → OUR mesh verifies → 06_heal_lora on the kept set")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    print("  wire: distill(domain, teacher_fn, problems) → verified SFT data → scripts/06_heal_lora.py")


if __name__ == "__main__":
    main()
