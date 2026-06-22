#!/usr/bin/env python3
"""Code-RAG retrieval server — exposes `search_code` as an agent tool.

  python scripts/11_rag_server.py --index rag/index --port 8090
  # quick test without serving:
  python scripts/11_rag_server.py --index rag/index --query "retry with backoff"

The agent decides WHEN to retrieve (agentic-native). Register this tool in your
harness (the schema is printed on startup), point its executor at POST /search,
and the model can pull just the relevant code instead of whole-repo dumps:
smarter, faster, less context.
"""

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import rag  # noqa: E402

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_code",
        "description": ("Search the indexed codebase for relevant code. Use "
                        "before editing/answering to pull the few relevant "
                        "files instead of guessing. Returns file:lines + code."),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "what to find (symbols, behavior, intent)"},
                "k": {"type": "integer", "description": "max results (default 6)"},
            },
            "required": ["query"],
        },
    },
}


def fmt(results):
    """Compact, citeable text block for injection into the agent context."""
    out = []
    for r in results:
        out.append(f"// {r['file']}:{r['lines']}  [{r['lang']}] {r['symbol']}\n"
                   f"{r['text']}")
    return "\n\n".join(out)


def make_handler(retriever):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            res = retriever.search(body.get("query", ""), int(body.get("k", 6)))
            payload = json.dumps({"results": res, "text": fmt(res)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)
    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=os.path.join(HERE, "..", "rag", "index"))
    ap.add_argument("--port", type=int, default=8090)
    ap.add_argument("--query", default=None, help="one-shot search, then exit")
    ap.add_argument("--k", type=int, default=6)
    args = ap.parse_args()

    chunks = rag.load_index(args.index)
    print(f">> Loaded {len(chunks)} chunks from {args.index}")
    retriever = rag.Retriever(chunks)

    if args.query:
        for r in retriever.search(args.query, args.k):
            head = r["text"].splitlines()[0][:70] if r["text"] else ""
            print(f"  {r['score']:6.3f}  {r['file']}:{r['lines']}  "
                  f"[{r['lang']}] {head}")
        return

    print(">> Register this tool in your agent harness:")
    print(json.dumps(TOOL_SCHEMA, indent=2))
    print(f">> search_code -> POST http://localhost:{args.port}/search "
          f'{{"query": "...", "k": 6}}')
    ThreadingHTTPServer(("0.0.0.0", args.port), make_handler(retriever)).serve_forever()


if __name__ == "__main__":
    main()
