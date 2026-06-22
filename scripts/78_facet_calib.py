#!/usr/bin/env python3
"""#23 facet-inclusive REAP calibration mix — protect EVERY facet's experts in the next prune.

The v4 prune used a CODE-FIRST calibration → it cost design soul (the aesthetic experts weren't exercised, so
REAP saliency under-weighted them). The deepest fix isn't healing design back — it's calibrating the prune on
ALL facets so their experts survive in the first place. This assembles a balanced calibration covering the 7
facets (design/dataviz/code/security/math/prose/architecture) + core capabilities, anchored on the elite gold
seeds (the canonical signal that fires each facet's experts). Feeds scripts/23_stream_calibrate for the re-prune.

  python scripts/78_facet_calib.py
"""
import glob
import json
import os
import random
import sys
from collections import Counter

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
random.seed(0)


def _text(row):
    return "\n".join(m.get("content", "") for m in row.get("messages", []) if m.get("content"))


def _sample(rel, k):
    fp = os.path.join(ROOT, rel)
    if not os.path.exists(fp):
        return []
    rows = [json.loads(line) for line in open(fp) if line.strip()]
    random.shuffle(rows)
    out = [_text(r) for r in rows]
    return [t for t in out if t][:k]


def main():
    mix = []
    # 1) the elite facet seeds — the canonical exemplar that exercises each facet's experts (the key signal)
    for fp in sorted(glob.glob(os.path.join(ROOT, "heal/facets/seeds/*"))):
        if not os.path.isfile(fp) or fp.endswith(".pyc"):
            continue
        mix.append((os.path.basename(fp).split("_")[0], open(fp, encoding="utf-8", errors="ignore").read()))
    for t in _sample("heal/design/seeds.jsonl", 9):
        mix.append(("design", t))
    # the facet CANONS — dense facet vocabulary (OKLCH/Tufte/Saltzer/Erdős/…), a strong per-facet REAP activator
    # that exercises each facet's experts so a harder prune (14/7GB) keeps them. Full balance comes from the flywheel.
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from soul import FACETS  # noqa: E402
    for name, facet in FACETS.items():
        mix.append((name, facet.canon))
    # 2) balanced samples per capability from the heal corpora
    for cap, rel, k in [("design", "heal/design/train.jsonl", 40),
                        ("math", "heal/lean/train.jsonl", 40),
                        ("retrieval", "heal/callsieve/train.jsonl", 40)]:
        for t in _sample(rel, k):
            mix.append((cap, t))
    # 3) scale GENERAL to the Unsloth Dynamic-2.0 bar: ≥1.5M CONVERSATIONAL tokens (heal/data-v4 is instruct
    # {messages} — the right kind, NOT text-only). More calib → better REAP saliency (23) AND lower quant KL (#60).
    target_tokens = int(os.environ.get("CALIB_TOKENS", 1_500_000))
    cur = sum(len(t[:4000]) // 4 for _, t in mix)            # ~4 chars/token, samples are capped at 4000 chars on write
    for t in _sample("heal/data-v4/train.jsonl", 8000):
        if cur >= target_tokens:
            break
        mix.append(("general", t))
        cur += len(t[:4000]) // 4
    random.shuffle(mix)

    out = os.path.join(ROOT, "calib", "facet_mix.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        for cap, text in mix:
            f.write(json.dumps({"text": text[:4000], "facet": cap}) + "\n")

    counts = Counter(c for c, _ in mix)
    print(f"  facet-inclusive calibration: {len(mix)} samples → {out}")
    for cap, n in counts.most_common():
        print(f"    {cap:13s}: {n}")
    facets = {"design", "dataviz", "code", "security", "math", "prose", "architecture"}
    covered = facets & set(counts)
    print(f"  facet coverage: {len(covered)}/7 {sorted(covered)}")
    print("  → REAP saliency on THIS keeps every facet's experts; the next prune loses no soul (the deepest fix)")
    assert len(mix) > 100 and len(covered) >= 6, (len(mix), covered)


if __name__ == "__main__":
    main()
