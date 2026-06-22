#!/usr/bin/env python3
"""Build heal/soul/{train,valid}.jsonl — the SIZE-AGNOSTIC heal corpus the Demolition family re-heals on.

Merges (1) the soul-flywheel per-facet outputs (heal/*/soul.jsonl, when they exist — GPU-produced) + (2) the
hand-authored gold seeds (the canonical elite exemplar per facet) + (3) the design seeds, into MLX-LM chat format.
Re-run after 77_soul_flywheel enriches each facet — it's the same corpus at every family size, so every size
re-heals elite. Feeds: 06_heal_lora --data heal/soul --skip-data. CPU.

  python scripts/83_build_soul_corpus.py
"""
import glob
import json
import os

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")

FACET_PROMPT = {
    "code": "Write clean, idiomatic, production-ready code (Kernighan & Pike clarity).",
    "design": "Design an elite, bespoke UI — OKLCH only, 8px grid, modular type scale, no frameworks.",
    "dataviz": "Create a Tufte-clean data visualization — maximize data-ink, no chartjunk.",
    "math": "Write an elegant, correct, machine-checkable formal proof.",
    "prose": "Write clear, concise prose (Strunk & White — omit needless words).",
    "research": "Answer with grounded, cited, appropriately-hedged claims (Feynman: don't fool yourself).",
    "security": "Write secure code — no hard-coded secrets, parameterized queries, least privilege.",
    "architecture": "Design clean architecture — ports/adapters, clear boundaries (Alexander/Cockburn).",
}


def collect():
    out, seen = [], set()

    def add(row):
        key = json.dumps(row, sort_keys=True)
        if "messages" in row and key not in seen:
            seen.add(key)
            out.append(row)

    for fp in glob.glob(os.path.join(ROOT, "heal", "*", "soul.jsonl")):     # (1) flywheel output (GPU), if present
        for line in open(fp, encoding="utf-8", errors="ignore"):
            try:
                add(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    for fp in sorted(glob.glob(os.path.join(ROOT, "heal", "facets", "seeds", "*"))):   # (2) gold seeds
        if not os.path.isfile(fp) or fp.endswith(".pyc"):
            continue
        facet = os.path.basename(fp).split("_")[0]
        body = open(fp, encoding="utf-8", errors="ignore").read()
        add({"messages": [{"role": "user", "content": FACET_PROMPT.get(facet, "Produce elite, idiomatic work.")},
                          {"role": "assistant", "content": body}]})
    ds = os.path.join(ROOT, "heal", "design", "seeds.jsonl")                  # (3) design seeds
    if os.path.exists(ds):
        for line in open(ds, encoding="utf-8", errors="ignore"):
            try:
                add(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return out


def main():
    rows = collect()
    d = os.path.join(ROOT, "heal", "soul")
    os.makedirs(d, exist_ok=True)
    nval = max(1, len(rows) // 10)
    with open(os.path.join(d, "train.jsonl"), "w") as f:
        for r in rows[nval:]:                    # train DISJOINT from valid — no leakage (valid was a subset before)
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(d, "valid.jsonl"), "w") as f:
        for r in rows[:nval]:
            f.write(json.dumps(r) + "\n")
    print(f"  heal/soul/train.jsonl: {len(rows)} examples ({nval} valid) — flywheel soul.jsonl + gold seeds + design seeds")
    print("  → re-run after 77_soul_flywheel enriches each facet; 06_heal_lora --data heal/soul --skip-data")
    assert rows, "no soul corpus assembled — check heal/facets/seeds/"


if __name__ == "__main__":
    main()
