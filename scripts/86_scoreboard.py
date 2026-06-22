#!/usr/bin/env python3
"""Scoreboard — keep EVERY benchmark score over time so you can SEE progress (the honest before→after of tuning).

Each run appends {date, benchmark, iteration, solved, total, rate, split, study_set, note} to scores.jsonl, and
show() prints the per-benchmark progression so the model getting smarter is visible across expert-iteration cycles.
HONESTY GUARD: the `split` scored here must be the TEST set, and `study_set` records what was trained on — if they
overlap, that's contamination (a fake number). record() refuses test==study.

  python scripts/86_scoreboard.py --record miniF2F --solved 30 --total 226 --iter 0 --note baseline
  python scripts/86_scoreboard.py --record miniF2F --solved 62 --total 226 --iter 1 --study "miniF2F-valid+Lean-Workbook" --note "after expert-iter"
  python scripts/86_scoreboard.py --show
"""
import argparse
import datetime
import json
import os

HERE = os.path.dirname(__file__)
SCORES = os.path.join(HERE, "..", "scores.jsonl")


def record(benchmark, solved, total, iteration=0, split="test", study_set="", note=""):
    import re
    bad = {split.strip().lower(), f"{benchmark.strip().lower()}-{split.strip().lower()}"}
    toks = {t for t in re.split(r"[+,\s]+", study_set.strip().lower()) if t}   # tokenize: a compound "test+x" can't sneak by
    assert not (toks & bad), \
        f"CONTAMINATION: study_set '{study_set}' includes the scored test split '{split}' — that's a fake number"
    row = {"date": datetime.date.today().isoformat(), "benchmark": benchmark, "iteration": int(iteration),
           "solved": int(solved), "total": int(total), "rate": round(100 * solved / max(total, 1), 1),
           "split": split, "study_set": study_set, "note": note}
    with open(SCORES, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def show():
    if not os.path.exists(SCORES):
        print("  no scores recorded yet")
        return
    from collections import defaultdict
    rows = []
    with open(SCORES) as f:
        for line in f:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue                       # tolerate a partial/corrupt line from an interrupted write
    by = defaultdict(list)
    for r in rows:
        by[r["benchmark"]].append(r)
    print(f"  {'benchmark':24s} progression (rate% by iteration)            Δ")
    print(f"  {'-' * 24} {'-' * 44} {'-' * 6}")
    for b, rs in sorted(by.items()):
        rs.sort(key=lambda x: x["iteration"])
        prog = "  →  ".join(f"i{r['iteration']}:{r['rate']}% ({r['solved']}/{r['total']})" for r in rs)
        delta = (rs[-1]["rate"] - rs[0]["rate"]) if len(rs) > 1 else 0.0
        print(f"  {b:24s} {prog:44s} {delta:+5.1f}")


def _selftest():
    global SCORES
    import tempfile
    SCORES = tempfile.mktemp(suffix=".jsonl")
    record("miniF2F", 30, 226, 0, note="baseline")
    record("miniF2F", 62, 226, 1, study_set="miniF2F-valid+Lean-Workbook", note="after expert-iter (study⟂test)")
    try:
        record("miniF2F", 200, 226, 2, study_set="miniF2F-test")          # must be REFUSED (studied the exam)
        ok = False
    except AssertionError:
        ok = True
    assert ok, "contamination guard failed to catch study==test"
    rows = [json.loads(line) for line in open(SCORES)]
    assert len(rows) == 2 and rows[1]["rate"] > rows[0]["rate"]
    show()
    print("  scoreboard selftest PASS — records + shows progression; REFUSES studying the test set (honesty guard)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", default="")
    ap.add_argument("--solved", type=int, default=0)
    ap.add_argument("--total", type=int, default=0)
    ap.add_argument("--iter", type=int, default=0)
    ap.add_argument("--split", default="test")
    ap.add_argument("--study", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if a.record:
        print("  recorded:", record(a.record, a.solved, a.total, a.iter, a.split, a.study, a.note))
    show()


if __name__ == "__main__":
    main()
