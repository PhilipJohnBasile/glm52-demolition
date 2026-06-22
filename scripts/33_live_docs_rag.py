#!/usr/bin/env python3
"""Live-docs RAG — index CURRENT documentation so the model retrieves API truth
instead of hallucinating it. This is how we beat Fable's training cutoff and
deliver 'latest and greatest' on YOUR stack (TS 7, Postgres, modern web platform).
Fetches a configurable doc manifest, chunks with src/rag, and merges into the
hybrid index (BM25 + fastembed) that the code-rag MCP serves.

  python scripts/33_live_docs_rag.py                       # default stack manifest
  python scripts/33_live_docs_rag.py --url URL --name NAME # add one source
  python scripts/33_live_docs_rag.py --manifest docs.json  # {name: url, ...}
"""
import argparse
import json
import os
import re
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import rag  # noqa: E402

# YOUR stack, current: latest TS, Postgres, and the modern web-platform APIs we
# trained the model to prefer (so retrieval confirms the live signatures).
DEFAULT_SOURCES = {
    "TypeScript 5.x/7 release notes": "https://www.typescriptlang.org/docs/handbook/release-notes/overview.html",
    "TypeScript handbook — everyday types": "https://www.typescriptlang.org/docs/handbook/2/everyday-types.html",
    "PostgreSQL 17 — SQL commands": "https://www.postgresql.org/docs/current/sql-commands.html",
    "PostgreSQL 17 — functions": "https://www.postgresql.org/docs/current/functions.html",
    "MDN — Popover API": "https://developer.mozilla.org/en-US/docs/Web/API/Popover_API",
    "MDN — CSS anchor positioning": "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_anchor_positioning",
    "MDN — Temporal": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Temporal",
    "MDN — View Transition API": "https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API",
    "MDN — scroll-driven animations": "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_scroll-driven_animations",
    "MDN — :has()": "https://developer.mozilla.org/en-US/docs/Web/CSS/:has",
}

_TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
_HTML = re.compile(r"</?[a-zA-Z][^>]*>")        # require a letter after '<' so prose/code 'a < b' isn't stripped as a tag
_WS = re.compile(r"\n{3,}")


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rag-docs)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "ignore")
    raw = _TAG.sub(" ", raw)
    text = _HTML.sub("", raw)
    text = re.sub(r"&[a-z]+;", " ", text)
    return _WS.sub("\n\n", text).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=os.path.join(HERE, "..", "rag", "index"))
    ap.add_argument("--manifest", help="JSON {name: url}")
    ap.add_argument("--url")
    ap.add_argument("--name")
    args = ap.parse_args()
    sources = dict(DEFAULT_SOURCES)
    if args.manifest:
        sources = json.load(open(args.manifest))
    if args.url:
        sources = {args.name or args.url: args.url}

    new_chunks = []
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for name, url in sources.items():
            try:
                text = fetch(url)
                if len(text) < 200:
                    print(f"  [skip] {name}: too short"); continue
                p = os.path.join(d, re.sub(r"\W+", "_", name)[:60] + ".md")
                open(p, "w").write(f"# {name}\nSource: {url}\n\n{text[:200000]}")
                paths.append(p)
                print(f"  fetched {name} ({len(text)//1000}k chars)")
            except Exception as e:  # noqa: BLE001
                print(f"  [skip] {name}: {str(e)[:60]}")
        if paths:
            new_chunks = rag.index_paths(paths, langs=["markdown"] * len(paths))
            for c in new_chunks:                  # tag provenance so docs are identifiable
                c["doc"] = True

    # merge into the existing index (dedupe by file+span), then the code-rag MCP
    # rebuilds embeddings on next load (cache keys on chunk count).
    cf = os.path.join(args.index, "chunks.jsonl")
    existing = rag.load_index(args.index) if os.path.exists(cf) else []
    def _key(c):                          # basename is STABLE across runs; full path is a per-run temp dir (UUID) → never dedups
        return (os.path.basename(c["file"]), c.get("start_line"), c.get("end_line"))
    seen = {_key(c) for c in existing}
    added = [c for c in new_chunks if _key(c) not in seen]
    rag.save_index(existing + added, args.index)
    print(f"\n  +{len(added)} doc chunks -> {args.index} (total {len(existing)+len(added)})")
    print("  the code-rag MCP now retrieves CURRENT API docs; restart it to rebuild embeddings.")


if __name__ == "__main__":
    main()
