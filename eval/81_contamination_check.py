#!/usr/bin/env python3
"""Benchmark contamination check (eval honesty) — are miniF2F TEST problems in our Lean TRAINING data?

If a test theorem's GOAL appears in training, a 'solved' may be MEMORIZED rather than reasoned → the reported
miniF2F number would be inflated. Standard practice (GPT-3/Llama/lm-eval): normalized exact-match of the test
item against training, name-agnostic (the math statement matters, not the theorem name). CPU-only; run before
publishing the number so it stays honest.

  python scripts/81_contamination_check.py
"""
import glob
import json
import os
import re

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")


def goal_of(stmt: str) -> str:
    """Name-agnostic normalized GOAL: drop the theorem/lemma name, keep the signature up to ':=', collapse
    whitespace, lowercase. Two problems with the same goal under different names → the same key (= contamination)."""
    head = stmt.split(":=")[0]
    head = re.sub(r"\b(?:theorem|lemma)\s+[\w'.]+", "thm", head)   # erase the name
    return re.sub(r"\s+", " ", head).strip().lower()


def load_train_goals():
    goals = {}
    for fp in glob.glob(os.path.join(ROOT, "heal", "lean*", "train.jsonl")) + \
              glob.glob(os.path.join(ROOT, "heal", "rft-math", "train.jsonl")):
        for line in open(fp, encoding="utf-8", errors="ignore"):
            try:
                text = " ".join(m.get("content", "") for m in json.loads(line).get("messages", []))
            except Exception:  # noqa: BLE001
                continue
            for m in re.finditer(r"(?:theorem|lemma)\s+[\w'.]+[^=]*?:=", text):
                goals.setdefault(goal_of(m.group(0)), os.path.basename(fp))
    return goals


def load_minif2f_test():
    from datasets import load_dataset
    for name in ["cat-searcher/minif2f-lean4", "brando/minif2f-lean4", "internlm/miniF2F-lean4"]:
        try:
            ds = load_dataset(name, split="test")
            break
        except Exception:  # noqa: BLE001
            ds = None
    out = []
    for row in ds or []:
        s = (row.get("formal_statement") or row.get("statement") or row.get("lean4") or "").strip()
        if s.startswith(("theorem", "lemma")):
            out.append(s.split(":=")[0].strip())
    return out


def _toks(s):
    return frozenset(re.findall(r"[A-Za-z0-9]+|[≤≥<>=+\-*/^∑∏√]", s))


def main():
    train = load_train_goals()
    test = load_minif2f_test()
    exact = [(t, train[goal_of(t)]) for t in test if goal_of(t) in train]
    # near-duplicate (paraphrase) pass: token-Jaccard > 0.8 against any training goal (exact-match can miss these)
    train_tok = [_toks(g) for g in train]
    near = []
    for t in test:
        if goal_of(t) in train:
            continue
        tt = _toks(goal_of(t))
        if len(tt) >= 4 and any(len(tt & gt) / len(tt | gt) > 0.8 for gt in train_tok):
            near.append(t)
    print(f"  miniF2F-test problems: {len(test)} | distinct training-Lean goals: {len(train)}")
    print(f"  EXACT-goal contamination: {len(exact)}/{len(test)} = {100 * len(exact) / max(len(test), 1):.1f}%")
    print(f"  NEAR-dup (Jaccard>0.8):   {len(near)}/{len(test)} = {100 * len(near) / max(len(test), 1):.1f}%")
    for t, src in exact[:4]:
        print(f"    ⚠ exact: {t[:60]}  ← {src}")
    for t in near[:4]:
        print(f"    ~ near:  {t[:60]}")
    if not exact and not near:
        print("  ✓ CLEAN (exact + near-dup) — no miniF2F test problem in training. Number is HONEST (reasoned, not memorized).")
    else:
        print(f"  ⚠ {len(exact) + len(near)} overlapping — exclude from pass@ or report clean-vs-contaminated separately.")
    return len(exact) + len(near), len(test)


if __name__ == "__main__":
    main()
