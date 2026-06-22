#!/usr/bin/env python3
"""Build a LANGUAGE-FOCUSED, AGENTIC calibration set for REAP.

Target stack: TypeScript, JavaScript, Python, Rust, Dart.

The prune keeps the experts that fire on this data, so its composition *is* the
spec for the demolished model. Three pillars, in priority order:

  1. AGENTIC traces (tool calls, diffs, multi-turn edits) — weighted highest.
     Without these you prune away tool-use behavior and break the agent loop,
     no matter how good the raw-code experts are.
  2. Per-language code — weighted to protect the scarce languages. Dart and Rust
     are under-represented in the base model, so they get the heaviest weights
     or they get pruned out first.
  3. Glue formats the agent must READ in these repos (JSON/YAML/TOML/Cargo.toml/
     pubspec.yaml/SQL/Bash/Dockerfile/HTML/CSS).

Your OWN traces in calibration/mine/ override everything — they're the best
possible signal. Drop real agent transcripts / repo files there.

Output: calibration/calib.jsonl  ({"text","lang","kind"} lines).
"""

import argparse
import glob
import json
import os
import random

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "calibration", "calib.jsonl")

# English-only natural language. GLM-5.2 is heavily bilingual (Chinese); by
# calibrating English-only, Chinese/other-script experts get ~zero activation
# and REAP prunes them FIRST -> big prune headroom. Code (ASCII) always passes.
_FOREIGN = [(0x4E00, 0x9FFF), (0x3400, 0x4DBF),   # CJK ideographs
            (0x3040, 0x30FF),                      # hiragana/katakana
            (0xAC00, 0xD7AF),                      # hangul
            (0x0400, 0x04FF),                      # cyrillic
            (0x0600, 0x06FF), (0x0590, 0x05FF)]    # arabic / hebrew


def is_english(text, max_foreign=0.02):
    if not text:
        return False
    foreign = letters = 0
    for c in text:
        o = ord(c)
        if c.isalpha():
            letters += 1
            if any(lo <= o <= hi for lo, hi in _FOREIGN):
                foreign += 1
    if letters == 0:
        return True   # pure code/symbols
    return foreign / letters <= max_foreign

# Weight = how strongly to protect this language from pruning.
# Higher for the less-represented langs (Rust) so their experts survive.
LANG_WEIGHTS = {
    "python": 1.0,
    "typescript": 0.8,
    "javascript": 0.5,   # overlaps TS expert territory; low marginal cost
    "go": 0.9,           # well represented, fairly self-contained
    "rust": 1.2,         # least represented of this set -> protect most
    "html": 0.9,         # first-class generation target (hand-written UI)
    "css": 0.9,          # first-class: modern flexbox/grid, not just glue
}
GLUE_LANGS = ["json", "yaml", "toml", "sql", "bash", "dockerfile"]
GLUE_WEIGHT = 0.4
# === OFFICIAL CEREBRAS REAP agentic calibration recipe (ICLR 2026) ===
# 24,576 samples @ seq 16,384: 50% reasoning + coding + tool-calling + agentic
# trajectories. This is the PROVEN mix REAP uses (near-lossless to 50% prune).
# We layer OUR edges on top: modern 2026 repos, English-only, 7-lang focus, and a
# HEAL step (Cerebras publishes NO healing — our advantage, critical at our ratio).
RECIPE = {
    "reasoning": ("open-r1/Mixture-of-Thoughts", 12288),   # 50% — code/math/sci
    "coding":    ("theblackcat102/evol-codealpaca-v1", 4096),
    "tool":      ("Salesforce/xlam-function-calling-60k", 4096),
    "agentic":   ("SWE-bench/SWE-smith-trajectories", 4096),  # real SWE trajectories
}
RECIPE_MAXLEN_CHARS = 60000   # ~16k tokens per the REAP recipe
MODERN_WEIGHT = 2.0           # our modern-code primary signal layered on top
CODE_DATASET = "bigcode/the-stack-smol"   # only for --include-legacy / glue


def load_mine():
    mine_dir = os.path.join(HERE, "..", "calibration", "mine")
    rows = []
    for p in glob.glob(os.path.join(mine_dir, "**", "*"), recursive=True):
        if not os.path.isfile(p):
            continue
        ext = os.path.splitext(p)[1].lower()
        lang = {".py": "python", ".ts": "typescript", ".tsx": "typescript",
                ".js": "javascript", ".jsx": "javascript", ".rs": "rust",
                ".go": "go", ".html": "html", ".htm": "html",
                ".css": "css", ".scss": "css", ".sass": "css"}.get(ext, "mixed")
        if ext == ".jsonl":
            for line in open(p, errors="ignore"):
                try:
                    o = json.loads(line)
                    t = o.get("text") or o.get("content") or ""
                    if t.strip():
                        rows.append({"text": t, "lang": o.get("lang", "mixed"),
                                     "kind": "mine"})
                except json.JSONDecodeError:
                    continue
        elif ext in (".txt", ".md", ".py", ".ts", ".tsx", ".js", ".jsx",
                     ".rs", ".go", ".html", ".htm", ".css", ".scss", ".sass"):
            txt = open(p, errors="ignore").read()
            if txt.strip():
                rows.append({"text": txt, "lang": lang, "kind": "mine"})
    return rows


def load_modern_repos(per_lang_base=350):
    """PRIMARY modern-version calibration source: idiomatic latest-version code
    (June 2026) from the curated repos. Biasing the prune toward modern idioms
    makes REAP keep modern-idiom experts and cut legacy-version ones — so we can
    cut deeper at the same quality. Function-level + English-only via rag chunker.
    """
    d = os.path.join(HERE, "..", "rag", "training_repos")
    if not os.path.isdir(d):
        print("  (no rag/training_repos — run scripts/19_fetch_training_repos.sh "
              "for modern-only calibration)")
        return []
    sys.path.insert(0, os.path.join(HERE, "..", "src"))
    import rag
    from collections import Counter
    cnt, rows = Counter(), []
    for c in rag.index_paths([d], langs=list(LANG_WEIGHTS.keys())):
        lang = c["lang"]
        if cnt[lang] >= per_lang_base * LANG_WEIGHTS.get(lang, 1):
            continue
        rows.append({"text": c["text"], "lang": lang, "kind": "modern"})
        cnt[lang] += 1
    print(f"  + {len(rows)} MODERN code chunks (latest versions) {dict(cnt)}")
    return rows


def take(ds_iter, n, lang, kind, maxlen=24000):
    out = []
    for ex in ds_iter:
        if len(out) >= n:
            break
        # robust field extraction across the recipe's varied datasets
        t = (ex.get("content") or ex.get("text") or ex.get("solution")
             or ex.get("response") or ex.get("answer"))
        if not isinstance(t, str) or not t:
            t = json.dumps(ex)            # messages/trajectories -> serialize
        if t.strip():
            out.append({"text": t[:maxlen], "lang": lang, "kind": kind})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-lang", type=int, default=120,
                    help="glue/legacy sample count per language")
    ap.add_argument("--recipe-scale", type=float, default=0.1,
                    help="fraction of the full Cerebras recipe (1.0 = 24,576 "
                         "samples; 0.1 ≈ 2,500, faster/less memory on a Mac)")
    ap.add_argument("--mine-repeat", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--include-legacy", action="store_true",
                    help="also calibrate on old public code (default: modern-only)")
    args = ap.parse_args()
    random.seed(args.seed)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    rows = []

    mine = load_mine()
    if mine:
        print(f"  + {len(mine)} of YOUR traces (x{args.mine_repeat}) — best signal")
        rows += mine * args.mine_repeat
    else:
        print("  (no calibration/mine/ — add your real agent transcripts there "
              "for the strongest prune)")

    # PRIMARY: modern latest-version code -> prune keeps modern-idiom experts,
    # cuts legacy-version ones (smaller model, modern-only).
    rows += load_modern_repos() * int(MODERN_WEIGHT)

    try:
        from datasets import load_dataset
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] `datasets` unavailable ({e}); writing mine-only set")
        load_dataset = None

    if load_dataset:
        # === Official Cerebras REAP recipe (scaled by --recipe-scale) ===
        # reasoning 50% + coding + tool-calling + agentic SWE trajectories.
        for kind, (ds_id, n) in RECIPE.items():
            n = max(1, int(n * args.recipe_scale))
            try:
                ds = load_dataset(ds_id, split="train", streaming=True)
                got = take(ds, n, "mixed", kind, maxlen=RECIPE_MAXLEN_CHARS)
                rows += got
                print(f"  + {len(got):5} {kind:10} from {ds_id}")
            except Exception as e:  # noqa: BLE001
                print(f"  [warn] {ds_id} failed: {str(e)[:60]}")

        # 2) LEGACY public code — OFF by default (modern-only). Enable with
        # --include-legacy if you need old-version syntax support. Excluding it
        # lets the prune cut legacy-version experts -> smaller model.
        if args.include_legacy:
            for lang, w in LANG_WEIGHTS.items():
                n = max(1, int(args.per_lang * w))
                try:
                    ds = load_dataset(CODE_DATASET, lang, split="train",
                                      streaming=True)
                    rows += take(ds, n, lang, "code")
                    print(f"  + {n} {lang} legacy-diversity (weight {w})")
                except Exception as e:  # noqa: BLE001
                    print(f"  [warn] {lang} from {CODE_DATASET}: {str(e)[:50]}")

        # 3) glue formats the agent must read
        for lang in GLUE_LANGS:
            n = max(1, int(args.per_lang * GLUE_WEIGHT))
            try:
                ds = load_dataset(CODE_DATASET, lang, split="train",
                                  streaming=True)
                rows += take(ds, n, lang, "glue")
            except Exception:  # noqa: BLE001
                pass
        print(f"  + glue formats: {', '.join(GLUE_LANGS)}")

    # English-only natural language (drops Chinese/other-script NL; keeps code).
    before = len(rows)
    rows = [r for r in rows if is_english(r["text"])]
    dropped = before - len(rows)
    print(f"  english-only filter: dropped {dropped}/{before} non-English rows "
          f"(those experts get pruned first -> more headroom)")

    random.shuffle(rows)
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    # summary by lang/kind so you can see the mix you're pruning toward
    from collections import Counter
    by_lang = Counter(r["lang"] for r in rows)
    by_kind = Counter(r["kind"] for r in rows)
    print(f"\n  wrote {len(rows)} rows -> {OUT}")
    print("  by kind:", dict(by_kind))
    print("  by lang:", dict(by_lang))


if __name__ == "__main__":
    main()
