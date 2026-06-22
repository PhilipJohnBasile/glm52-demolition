#!/usr/bin/env python3
"""Assemble a heal corpus from gold folders: dedup + shuffle + 95/5 split.

  python scripts/assemble_heal.py heal/_q_<name> soul_gold2 gold_fullstack ...
"""
import json
import glob
import os
import random
import sys

out = sys.argv[1]
folders = sys.argv[2:]
random.seed(42)
seen = set()
rows = []
for d in folders:
    for f in sorted(glob.glob(f"heal/{d}/*.jsonl")):
        for line in open(f):
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            key = json.dumps(
                [m.get("content", "") for m in o.get("messages", [])], sort_keys=True
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(o)
random.shuffle(rows)
n = len(rows)
v = max(8, n // 20)
os.makedirs(out, exist_ok=True)
with open(f"{out}/valid.jsonl", "w") as fh:
    fh.write("\n".join(json.dumps(r) for r in rows[:v]) + "\n")
with open(f"{out}/train.jsonl", "w") as fh:
    fh.write("\n".join(json.dumps(r) for r in rows[v:]) + "\n")
print(f"{out}: {n} unique -> {n - v} train / {v} valid")
