#!/usr/bin/env python3
"""Index your repos (or sample repos) for code RAG.

  python scripts/10_rag_index.py --repos rag/sample_repos --out rag/index
  python scripts/10_rag_index.py --repos ~/code/myproj ~/code/other --langs python rust
"""

import argparse
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import rag  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="+", required=True,
                    help="repo dirs (or files) to index")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "rag", "index"))
    ap.add_argument("--langs", nargs="*", default=None,
                    help="restrict to these langs (default: all supported)")
    args = ap.parse_args()

    print(f">> Indexing {args.repos} (langs={args.langs or 'all'})...")
    chunks = rag.index_paths(args.repos, langs=args.langs)
    if not chunks:
        sys.exit("  [stop] no indexable files found")
    rag.save_index(chunks, args.out)

    from collections import Counter
    by_lang = Counter(c["lang"] for c in chunks)
    by_file = len({c["file"] for c in chunks})
    print(f"  {len(chunks)} chunks from {by_file} files -> {args.out}")
    print("  by lang:", dict(by_lang))
    print(">> Serve retrieval:  python scripts/11_rag_server.py --index", args.out)


if __name__ == "__main__":
    main()
