#!/usr/bin/env python3
"""Controllable-thinking proxy in front of mlx_lm.server.

Thinking on this model is the highest-value capability for agentic coding, so we
KEEP it and gate it per request instead of eliminating it:

  * reasoning-heavy steps (plan / debug / implement / design)  -> thinking ON
  * trivial steps (run a tool, read a file, list, apply edit)  -> thinking OFF (fast)
  * explicit `/think` or `/nothink` token in the message        -> hard override
  * a soft token BUDGET so thinking stays fast and never blows the KV cache

Mechanism (all real, verified in mlx_lm.server 0.31.3):
  - toggle via request field  chat_template_kwargs={"enable_thinking": bool}
  - the server already separates reasoning text in responses
  - budget injected as a system instruction (soft); on/off is the hard lever

Run:
  MODEL=models/GLM-5.2-demolished-mxmix bash scripts/05_serve.sh   # upstream :8080
  python scripts/08_think_proxy.py --port 8081 --upstream http://localhost:8080
Point your agent harness at http://localhost:8081/v1 . Per-request override:
  add {"chat_template_kwargs":{"enable_thinking":true|false}} to force a mode.
"""

import argparse
import json
import re
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Heuristics for the default decision when the caller doesn't force a mode.
TRIVIAL = re.compile(r"\b(run|read|open|list|cat|grep|ls|show|print|get|fetch|"
                     r"apply|format|lint|cd|echo|head|tail|rename|move|delete)\b",
                     re.I)
REASON = re.compile(r"\b(plan|design|debug|fix|why|refactor|implement|architect|"
                    r"analyze|investigate|solve|optimize|design|reason|derive|"
                    r"explain|trace|root cause|strategy)\b", re.I)

CFG = {"upstream": "http://localhost:8080", "budget": 512, "default_on": True}


def decide_thinking(body):
    """Return (enable: bool, cleaned_messages, forced: bool)."""
    msgs = body.get("messages", [])
    # 1) explicit per-request override wins.
    ck = body.get("chat_template_kwargs") or {}
    if "enable_thinking" in ck:
        return bool(ck["enable_thinking"]), msgs, True

    last = ""
    for m in reversed(msgs):
        if m.get("role") == "user":
            last = m.get("content", "") if isinstance(m.get("content"), str) else ""
            break

    # 2) hard token overrides in the message.
    if "/nothink" in last:
        msgs = _strip(msgs, "/nothink")
        return False, msgs, True
    if "/think" in last:
        msgs = _strip(msgs, "/think")
        return True, msgs, True

    # 3) tool-result turns -> trivial -> off.
    if msgs and msgs[-1].get("role") in ("tool", "function"):
        return False, msgs, False

    # 4) keyword heuristic.
    if REASON.search(last):
        return True, msgs, False
    if TRIVIAL.search(last) and len(last) < 160:
        return False, msgs, False
    return CFG["default_on"], msgs, False


def _strip(msgs, token):
    out = []
    for m in msgs:
        c = m.get("content")
        if isinstance(c, str):
            m = {**m, "content": c.replace(token, "").strip()}
        out.append(m)
    return out


def apply_budget(msgs, budget):
    note = (f"Think concisely: use at most ~{budget} tokens of reasoning, then "
            f"give the answer.")
    sysmsgs = [i for i, m in enumerate(msgs) if m.get("role") == "system"]
    if sysmsgs:
        i = sysmsgs[0]
        msgs[i] = {**msgs[i], "content": msgs[i]["content"] + "\n" + note}
    else:
        msgs = [{"role": "system", "content": note}] + msgs
    return msgs


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _proxy(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        path = self.path

        if path.endswith("/chat/completions") and raw:
            try:
                body = json.loads(raw)
                enable, msgs, forced = decide_thinking(body)
                if enable and CFG["budget"]:
                    msgs = apply_budget(msgs, CFG["budget"])
                body["messages"] = msgs
                ck = body.get("chat_template_kwargs") or {}
                ck["enable_thinking"] = enable
                body["chat_template_kwargs"] = ck
                raw = json.dumps(body).encode()
                mode = "ON " if enable else "OFF"
                print(f"  think {mode}{'(forced)' if forced else '        '} "
                      f"<- {self.path}")
            except Exception as e:  # noqa: BLE001
                print(f"  [warn] passthrough (parse failed): {e}")

        up = urllib.request.Request(
            CFG["upstream"] + path, data=raw,
            headers={k: v for k, v in self.headers.items()
                     if k.lower() not in ("host", "content-length")},
            method=self.command)
        try:
            resp = urllib.request.urlopen(up, timeout=600)
        except urllib.error.HTTPError as e:
            resp = e
        self.send_response(resp.status)
        for k, v in resp.headers.items():
            if k.lower() not in ("transfer-encoding", "content-length",
                                 "connection"):
                self.send_header(k, v)
        self.end_headers()
        while True:
            chunk = resp.read(8192)
            if not chunk:
                break
            self.wfile.write(chunk)
            self.wfile.flush()

    do_POST = _proxy
    do_GET = _proxy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8081)
    ap.add_argument("--upstream", default="http://localhost:8080")
    ap.add_argument("--budget", type=int, default=512,
                    help="soft max reasoning tokens when thinking is ON (0=off)")
    ap.add_argument("--default-off", action="store_true",
                    help="default to no-think when ambiguous (default: think on)")
    args = ap.parse_args()
    CFG["upstream"] = args.upstream
    CFG["budget"] = args.budget
    CFG["default_on"] = not args.default_off
    print(f">> Controllable-thinking proxy on :{args.port} -> {args.upstream}")
    print(f"   default={'ON' if CFG['default_on'] else 'OFF'}, "
          f"budget={args.budget} reasoning tokens")
    print(f"   point your agent harness at http://localhost:{args.port}/v1")
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
