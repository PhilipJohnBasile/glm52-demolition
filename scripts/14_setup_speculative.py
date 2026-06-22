#!/usr/bin/env python3
"""Set up speculative decoding (1.5-2.5x) — and verify it will actually work.

Speculative decoding needs the draft model to share the TARGET's EXACT tokenizer
/vocabulary. If they differ, mlx_lm either errors or silently wastes the draft
(every token rejected). This helper checks compatibility BEFORE you commit, so
you don't ship a "speedup" that does nothing.

  # list candidate small GLM-family drafts to try
  python scripts/14_setup_speculative.py --suggest

  # verify a candidate against your target, then print the serve command
  python scripts/14_setup_speculative.py \
      --target models/GLM-5.2-demolished-mxmix \
      --draft  zai-org/GLM-4-9B    # example; must share GLM-5.2 tokenizer
"""

import argparse
import sys

# A draft must use the SAME tokenizer as GLM-5.2. Best candidates are small
# models from the same GLM-5 family / tokenizer lineage. Try these and verify.
SUGGESTIONS = [
    "zai-org/GLM-5-9B",          # if a small GLM-5 exists, ideal (same tokenizer)
    "zai-org/GLM-4.5-Air",       # same family; verify tokenizer matches
    "zai-org/GLM-4-9B",          # older; likely different vocab — verify!
]
TEST_STRINGS = [
    "def parse_config(path: str) -> dict:",
    "fn main() { println!(\"hello\"); }",
    "import { useState } from 'react';",
    "The quick brown fox jumps over 42 lazy dogs.",
    "<button class=\"btn\" onclick=\"submit()\">Go</button>",
]


def load_tok(repo):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(repo, trust_remote_code=True)


def compatible(target, draft):
    t, d = load_tok(target), load_tok(draft)
    if t.vocab_size != d.vocab_size:
        return False, f"vocab_size differs: target={t.vocab_size} draft={d.vocab_size}"
    mismatches = 0
    for s in TEST_STRINGS:
        if t.encode(s) != d.encode(s):
            mismatches += 1
    if mismatches:
        return False, f"{mismatches}/{len(TEST_STRINGS)} test strings tokenize differently"
    return True, "identical vocab_size and token ids on all probes"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suggest", action="store_true")
    ap.add_argument("--target", help="your demolished model dir/repo")
    ap.add_argument("--draft", help="candidate draft model repo/dir")
    ap.add_argument("--num-draft-tokens", type=int, default=4)
    args = ap.parse_args()

    if args.suggest:
        print("Candidate drafts (MUST share GLM-5.2's tokenizer — verify each):")
        for s in SUGGESTIONS:
            print("  -", s)
        print("\nVerify:  python scripts/14_setup_speculative.py "
              "--target <your-model> --draft <candidate>")
        return

    if not (args.target and args.draft):
        sys.exit("  need --target and --draft (or --suggest)")

    try:
        ok, why = compatible(args.target, args.draft)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"  [error] could not load tokenizers: {e}\n"
                 "  (pip install transformers; ensure both repos are accessible)")

    if not ok:
        print(f"  ❌ INCOMPATIBLE: {why}")
        print("  -> This draft would NOT speed you up (tokens get rejected).")
        print("     Find a small model that shares GLM-5.2's exact tokenizer.")
        sys.exit(1)

    print(f"  ✅ COMPATIBLE: {why}")
    print("  Serve with speculative decoding:")
    print(f"     DRAFT_MODEL={args.draft} NUM_DRAFT={args.num_draft_tokens} "
          f"MODEL={args.target} bash scripts/05_serve.sh")
    print("  Tune NUM_DRAFT (3-6): higher helps if the draft is accurate, hurts "
          "if it's often wrong. Benchmark tokens/sec both ways.")


if __name__ == "__main__":
    main()
