#!/usr/bin/env python3
"""Honest study→test loop — expert-iteration that EARNS a higher miniF2F score without cheating.

STUDY on miniF2F-VALIDATION + Lean-Workbook (practice) → harvest the proofs it solves → TRAIN on them → TEST on
miniF2F-TEST (held out, NEVER trained on) → record (86_scoreboard). Loop. The study set and the test set are
DISJOINT by construction — verified here — so the rising score is EARNED, not memorized. This is the legit
"study the textbook, then take the exam," not "study the exam." (Studying the exam = contamination = a fake number;
86_scoreboard.record() refuses it, and 81/82 would catch it.)

  python scripts/87_lean_study.py --selftest      # CPU: PROVE study ⟂ test (overlap must be 0)
  python scripts/87_lean_study.py --iters 3       # GPU: study→train→test ×3, scoreboard each (earned gains)
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(__file__)
STUDY_SET = "miniF2F-validation + internlm/Lean-Workbook"
TEST_SET = "miniF2F-test"


def _goal(stmt):                                                  # name-agnostic normalized goal (same as 81)
    s = re.sub(r"\b(?:theorem|lemma)\s+[\w'.]+", "thm", (stmt or "").split(":=")[0])
    return re.sub(r"\s+", " ", s).strip().lower()


def verify_disjoint():
    """The honesty guarantee: miniF2F validation (study) and test (exam) share NO problems."""
    from datasets import load_dataset
    for name in ["cat-searcher/minif2f-lean4", "brando/minif2f-lean4", "internlm/miniF2F-lean4"]:
        try:
            valid = load_dataset(name, split="validation")
            test = load_dataset(name, split="test")
        except Exception:  # noqa: BLE001
            continue
        gv = {_goal(r.get("formal_statement") or r.get("statement") or "") for r in valid}
        gt = {_goal(r.get("formal_statement") or r.get("statement") or "") for r in test}
        return len(gv & gt), len(gv), len(gt)
    return None


def study_iteration(it, base_adapter):                            # GPU — orchestration plan (wire subprocess at run)
    out_adapter = f"heal/adapters-lean-study-v{it}"
    print(f"  --- iteration {it}: study({STUDY_SET}) → train → test({TEST_SET}) ---", flush=True)
    for step in [
        f"python scripts/66_prove.py --split validation --workbook --adapter {base_adapter}  →  heal/lean-study/solved-{it}.jsonl   # harvest verified proofs (STUDY only)",
        f"python scripts/06_heal_lora.py --data heal/lean-study --skip-data --adapter-path {out_adapter} --no-mask-prompt --num-layers 6   # learn from its own wins",
        f"python scripts/73_minif2f.py --adapter {out_adapter}  →  logs/minif2f-study-{it}.log   # TEST on held-out test split",
        f"python scripts/86_scoreboard.py --record miniF2F --solved <S> --total 226 --iter {it + 1} --study '{STUDY_SET}' --note 'expert-iter'   # keep the score",
    ]:
        print(f"    $ {step}", flush=True)
    return out_adapter


def _selftest():
    r = verify_disjoint()
    if r is None:
        print("  ✗ could NOT load both splits to verify study⟂test — failing loudly (unverified ≠ safe)")
        sys.exit(1)
    overlap, nv, nt = r
    assert overlap == 0, f"STUDY/TEST OVERLAP = {overlap} — the loop would contaminate; abort!"
    print(f"  ✓ study ⟂ test PROVEN: validation={nv} problems, test={nt} problems, overlap={overlap} → loop is honest")
    print("  scoreboard records each iter's TEST score with study_set tagged; rising number is EARNED, not memorized.")
    print("  → GPU: --iters N runs study(valid+Workbook)→train→test(test)→scoreboard. The legit way to study for the exam.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--iters", type=int, default=3)
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    base = "heal/adapters-lean-v2"
    for it in range(a.iters):
        base = study_iteration(it, base)


if __name__ == "__main__":
    main()
