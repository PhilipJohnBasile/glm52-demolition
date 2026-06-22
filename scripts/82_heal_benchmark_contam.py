#!/usr/bin/env python3
"""Benchmark contamination check #2 — are the EVAL benchmarks we report (HumanEval, GSM8K) present in our HEAL
TRAINING data? The heal corpus is built from external datasets (open-r1/Mixture-of-Thoughts, OpenThoughts-114k,
evol-codealpaca, ultrachat, ...) which CAN include benchmark problems → the card's HumanEval 19/20 + GSM8K 8/12
could be inflated by memorization. This checks the HEADLINE numbers honestly (normalized-substring match of each
benchmark prompt against the whole heal corpus). CPU-only.

  python scripts/82_heal_benchmark_contam.py
"""
import glob
import json
import os
import re

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")


def heal_corpus():
    chunks = []
    for fp in glob.glob(os.path.join(ROOT, "heal", "*", "train.jsonl")):
        for line in open(fp, encoding="utf-8", errors="ignore"):
            try:
                for m in json.loads(line).get("messages", []):
                    chunks.append(m.get("content", "") or "")
            except Exception:  # noqa: BLE001
                continue
    return re.sub(r"\s+", " ", " ".join(chunks)).lower()


def main():
    text = heal_corpus()
    print(f"  heal corpus: {len(text) / 1e6:.1f}M chars (all heal/*/train.jsonl)")
    from datasets import load_dataset

    # HumanEval — the card's headline 19/20. Distinctive chunk = the normalized prompt's first ~90 chars (def + docstring start)
    try:
        he = load_dataset("openai/openai_humaneval", split="test")
        hits = sum(1 for r in he if (sig := re.sub(r"\s+", " ", r["prompt"]).strip().lower()[:90]) and sig in text)
        print(f"  HumanEval (164): {hits} prompts in heal = {100 * hits / 164:.1f}% contaminated "
              f"{'⚠ the 19/20 is inflated' if hits else '✓ CLEAN — 19/20 is honest'}")
    except Exception as e:  # noqa: BLE001
        print(f"  HumanEval: load failed ({e})")

    # GSM8K test — the card's 8/12 (sample 300 for speed)
    try:
        gsm = list(load_dataset("openai/gsm8k", "main", split="test"))[:300]
        hits = sum(1 for r in gsm if (q := re.sub(r"\s+", " ", r["question"]).strip().lower()[:90]) and q in text)
        print(f"  GSM8K-test (300 sampled): {hits} questions in heal = {100 * hits / 300:.1f}% contaminated "
              f"{'⚠ flag GSM8K' if hits else '✓ CLEAN'}")
    except Exception as e:  # noqa: BLE001
        print(f"  GSM8K: load failed ({e})")


if __name__ == "__main__":
    main()
