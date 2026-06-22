#!/usr/bin/env python3
"""Minimal MCP (stdio) server exposing `search_code` over the local RAG index,
so MCP-capable agent harnesses (Claude Code, Cline, opencode, Zed) can call it
directly — the agent decides when to retrieve.

Transport: newline-delimited JSON-RPC 2.0 over stdio (the MCP stdio convention).
No deps beyond stdlib + our rag module.

Register (Claude Code example, .mcp.json):
  { "mcpServers": { "code-rag": {
      "command": "python",
      "args": ["scripts/16_rag_mcp.py", "--index", "rag/index"] } } }
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import rag  # noqa: E402

PROTOCOL = "2024-11-05"
TOOL = {
    "name": "search_code",
    "description": ("Search the indexed codebase for relevant code. Call before "
                    "editing/answering to pull the few relevant files instead of "
                    "guessing. Returns file:lines + code."),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "what to find"},
            "k": {"type": "integer", "description": "max results (default 6)"},
        },
        "required": ["query"],
    },
}


def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=os.path.join(HERE, "..", "rag", "index"))
    ap.add_argument("--no-embeddings", action="store_true",
                    help="BM25 only; skip the semantic (fastembed) hybrid fallback")
    args = ap.parse_args()
    retriever = rag.Retriever(rag.load_index(args.index))
    if not args.no_embeddings:
        ok = retriever.enable_embeddings(args.index)   # index dir doubles as emb cache
        sys.stderr.write("[code-rag] semantic embeddings "
                         + ("ON (hybrid BM25+vectors)\n" if ok
                            else "unavailable -> BM25-only (pip install fastembed)\n"))

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method, mid = req.get("method"), req.get("id")

        if method == "initialize":
            send({"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "code-rag", "version": "0.1.0"}}})
        elif method == "notifications/initialized":
            continue  # notification, no response
        elif method == "tools/list":
            send({"jsonrpc": "2.0", "id": mid, "result": {"tools": [TOOL]}})
        elif method == "tools/call":
            params = req.get("params", {})
            if params.get("name") != "search_code":
                send({"jsonrpc": "2.0", "id": mid,
                      "error": {"code": -32601, "message": "unknown tool"}})
                continue
            a = params.get("arguments", {})
            results = retriever.search(a.get("query", ""), int(a.get("k", 6)))
            text = "\n\n".join(
                f"// {r['file']}:{r['lines']} [{r['lang']}] {r['symbol']}\n{r['text']}"
                for r in results) or "(no matches)"
            send({"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": text}]}})
        elif mid is not None:
            send({"jsonrpc": "2.0", "id": mid,
                  "error": {"code": -32601, "message": f"unknown method {method}"}})


if __name__ == "__main__":
    main()
