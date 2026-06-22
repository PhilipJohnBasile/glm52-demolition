#!/usr/bin/env python3
"""Build the ONE balanced mixed heal corpus — the research-mandated fix for catastrophic
forgetting (arxiv 2512.13706: balanced ~1:1 mixing across domains *eliminates* forgetting;
separate per-domain heals destroy other skills). One corpus, all domains, capped to ~equal
counts so no domain dominates and none is forgotten. SFT adds the skills; RFT sharpens after.

Domains (each a tagged source list; missing sources are skipped, not fatal):
  code     — your repo (callsieve own-repo pairs) + verified code-RFT passes
  math     — verified math-RFT traces + R1 reasoning + (later) Lean proofs
  design   — the design canon (principles + examples)
  general  — glue from the v4 heal corpus (anti-forgetting ballast)

  python scripts/66_build_mixed_corpus.py --dry-run     # report composition, write nothing (SAFE)
  python scripts/66_build_mixed_corpus.py --cap 4000    # build heal/data-mixed, ~cap rows/domain
"""
import argparse
import glob
import json
import os
import random

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "heal", "data-mixed")

# domain -> source jsonl globs (first-found wins; all that exist are used). Tag-based = reliable.
SOURCES = {
    "code": ["heal/callsieve/train.jsonl", "heal/code-rft/train.jsonl"],
    "math": ["heal/rft-math/train.jsonl", "heal/math/train.jsonl", "heal/lean/train.jsonl"],
    "design": ["heal/design/train.jsonl", "heal/canon/train.jsonl"],
    "general": ["heal/data-v4/train.jsonl"],   # the existing v4 mix = ballast
}


def _read(path, limit):
    rows = []
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return rows
    with open(full) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(rows) >= limit:
                break
    return rows


def build(cap, dry):
    random.seed(0)
    by_domain, found = {}, {}
    for dom, globs in SOURCES.items():
        rows = []
        for g in globs:
            for p in sorted(glob.glob(os.path.join(ROOT, g))):
                rel = os.path.relpath(p, ROOT)
                got = _read(rel, cap * 2)
                if got:
                    found.setdefault(dom, []).append(f"{rel}({len(got)})")
                    rows += got
        random.shuffle(rows)
        by_domain[dom] = rows[:cap]                 # cap each domain -> balance
    present = {d: r for d, r in by_domain.items() if r}
    if present:
        target = min(len(r) for r in present.values())   # balance to the smallest present domain
    else:
        target = 0
    mixed = []
    for dom, rows in present.items():
        mixed += [{**r, "_domain": dom} for r in rows[:target]]
    random.shuffle(mixed)

    print("  === mixed corpus composition (balanced for anti-forgetting) ===")
    for dom in SOURCES:
        srcs = ", ".join(found.get(dom, [])) or "— (no source yet)"
        n = min(len(by_domain.get(dom, [])), target) if by_domain.get(dom) else 0
        print(f"    {dom:8} -> {n:>5} rows   [{srcs}]")
    print(f"    {'TOTAL':8} -> {len(mixed):>5} rows ({len([d for d in present])} domains @ ~{target} each)")
    missing = [d for d in SOURCES if d not in present]
    if missing:
        print(f"  ⚠️ domains with NO data yet: {missing} — add their sources before the real build.")
    if dry:
        print("  (dry-run: nothing written)")
        return len(mixed)
    os.makedirs(OUT, exist_ok=True)
    nv = max(4, len(mixed) // 25)
    for name, part in [("valid.jsonl", mixed[:nv]), ("train.jsonl", mixed[nv:])]:
        with open(os.path.join(OUT, name), "w") as f:
            f.write("\n".join(json.dumps({k: v for k, v in r.items() if k != "_domain"}) for r in part))
    print(f"  wrote {len(mixed)} rows -> {OUT} (balanced; heal with scripts/06 --data heal/data-mixed)")
    return len(mixed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=4000, help="max rows per domain (then balanced to the min)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    build(args.cap, args.dry_run)


if __name__ == "__main__":
    main()
