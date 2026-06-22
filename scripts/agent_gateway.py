#!/usr/bin/env python3
"""Agent Gateway — makes the demolished GLM-5.2 a DROP-IN backend for any agent harness (aider, Cline,
Continue, Codex, Claude Code), the way Ollama exposes a model. Thin zero-dep proxy in front of
serve_stable (:8080) that adds the three things external tools need:

  1. SANE SAMPLING DEFAULTS  — temp 0.6 / top_p 0.95 / rep_pen 1.15 (a raw greedy request collapses the
     3-bit model into "a a a a"; tools don't know to set these, so we inject them).
  2. OpenAI FUNCTION-CALLING — accept `tools`, inject their schemas into the prompt, parse the model's
     tool intent back into OpenAI `tool_calls` (Cline/Codex/Continue agent mode need this).
  3. ANTHROPIC /v1/messages   — translate Anthropic <-> OpenAI so **Claude Code** runs on our model.

Run:  python scripts/agent_gateway.py            # listens :8090, proxies to :8080
Point any tool's base-url at  http://localhost:8090/v1   (OpenAI)  or  http://localhost:8090  (Anthropic).
"""
import json, os, re, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = os.environ.get("GATEWAY_UPSTREAM", "http://localhost:8080/v1")
PORT = int(os.environ.get("GATEWAY_PORT", "8090"))
DEFAULTS = {"temperature": 0.6, "top_p": 0.95, "repetition_penalty": 1.15}


def upstream_chat(body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(UPSTREAM + "/chat/completions", data, {"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def apply_defaults(body):
    for k, v in DEFAULTS.items():
        body.setdefault(k, v)
    body.setdefault("chat_template_kwargs", {}).setdefault("enable_thinking", False)
    return body


# ---- OpenAI function-calling: schemas -> prompt, model text -> tool_calls --------------------
def inject_tools(messages, tools):
    lines = ["You can call tools. To call one, reply with ONLY a line:",
             '<tool_call>{"name": "<tool>", "arguments": {<json args>}}</tool_call>',
             "Otherwise answer normally. Available tools:"]
    for t in tools:
        fn = t.get("function", t)
        lines.append(f"- {fn['name']}: {fn.get('description','')} params={json.dumps(fn.get('parameters',{}).get('properties',{}))}")
    sys_msg = {"role": "system", "content": "\n".join(lines)}
    return [sys_msg] + messages


def parse_tool_calls(text):
    """Pull tool calls out of the model's text (tolerate <tool_call> tags, ```json, or a bare {name,arguments})."""
    cand = None
    m = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", text, re.S) or re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        cand = m.group(1)
    else:
        m = re.search(r'(\{[^{}]*"name"\s*:[^{}]*"arguments"\s*:\s*\{.*?\}[^{}]*\})', text, re.S)
        cand = m.group(1) if m else None
    if not cand:
        return None
    try:
        obj = json.loads(cand)
        if "name" not in obj:
            return None
        args = obj.get("arguments", {})
        return [{"id": f"call_{abs(hash(cand)) % 10**8}", "type": "function",
                 "function": {"name": obj["name"], "arguments": json.dumps(args) if isinstance(args, dict) else str(args)}}]
    except Exception:
        return None


def validate_tool_call(tc, tools):
    """#45 schema-validate a parsed tool_call: known name + JSON args + required fields present."""
    if not tc:
        return False
    fn = tc[0]["function"]
    spec = next((t.get("function", t) for t in tools if t.get("function", t)["name"] == fn["name"]), None)
    if not spec:
        return False
    try:
        args = json.loads(fn["arguments"] or "{}")
    except Exception:
        return False
    required = spec.get("parameters", {}).get("required", [])
    return all(r in args for r in required)


def handle_openai_chat(body):
    tools = body.get("tools")
    body.pop("tool_choice", None)
    body.pop("model", None)   # serve serves its loaded model; client name (e.g. aider's) 404s
    if tools:
        body["temperature"] = min(body.get("temperature", 0.3), 0.3)   # decisive for structured tool output
    body = apply_defaults(body)
    resp = upstream_chat(body)                                          # NATIVE first: serve renders `tools`
    if tools:                                                           # via the restored GLM template + parses
        msg = resp["choices"][0]["message"]
        if not (msg.get("tool_calls") and validate_tool_call(msg["tool_calls"], tools)):
            # not native (or invalid) -> best-of-N inject + parse + #45 SCHEMA-VALIDATE, keep first valid
            fb = {k: v for k, v in body.items() if k != "tools"}
            fb["messages"] = inject_tools(body["messages"], tools)
            import concurrent.futures as _cf
            def _try(i):
                b = dict(fb); b["temperature"] = 0.2 + 0.15 * i
                r = upstream_chat(b)
                return parse_tool_calls(r["choices"][0]["message"].get("content") or "")
            with _cf.ThreadPoolExecutor(max_workers=4) as ex:          # concurrent (serve batches)
                cands = list(ex.map(_try, range(4)))
            valid = next((tc for tc in cands if validate_tool_call(tc, tools)), None)
            if valid:
                msg["tool_calls"] = valid
                msg["content"] = None
                resp["choices"][0]["finish_reason"] = "tool_calls"
    return resp


# ---- Anthropic /v1/messages <-> OpenAI (so Claude Code runs on our model) --------------------
def anthropic_to_openai(body):
    msgs = []
    if body.get("system"):
        sys = body["system"]
        msgs.append({"role": "system", "content": sys if isinstance(sys, str) else " ".join(b.get("text","") for b in sys)})
    for m in body.get("messages", []):
        c = m["content"]
        if isinstance(c, list):
            c = "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
        msgs.append({"role": m["role"], "content": c})
    ob = {"messages": msgs, "max_tokens": body.get("max_tokens", 1024)}
    if body.get("temperature") is not None:
        ob["temperature"] = body["temperature"]
    if body.get("tools"):
        ob["tools"] = [{"type": "function", "function": {"name": t["name"], "description": t.get("description", ""),
                        "parameters": t.get("input_schema", {})}} for t in body["tools"]]
    return ob


def openai_to_anthropic(resp, model):
    msg = resp["choices"][0]["message"]
    content = []
    if msg.get("tool_calls"):
        for tc in msg["tool_calls"]:
            content.append({"type": "tool_use", "id": tc["id"], "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"] or "{}")})
        stop = "tool_use"
    else:
        content.append({"type": "text", "text": msg.get("content") or ""})
        stop = "end_turn"
    return {"id": f"msg_{int(time.time())}", "type": "message", "role": "assistant", "model": model,
            "content": content, "stop_reason": stop,
            "usage": {"input_tokens": resp.get("usage", {}).get("prompt_tokens", 0),
                      "output_tokens": resp.get("usage", {}).get("completion_tokens", 0)}}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            try:
                req = urllib.request.Request(UPSTREAM + "/models")
                self._send(200, json.loads(urllib.request.urlopen(req, timeout=30).read()))
            except Exception as e:
                self._send(502, {"error": str(e)})
        else:
            self._send(200, {"status": "ok", "gateway": "glm5.2-demolition", "upstream": UPSTREAM})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
        try:
            if self.path.endswith("/v1/messages"):                       # Anthropic (Claude Code)
                model = body.get("model", "glm5.2")
                resp = handle_openai_chat(anthropic_to_openai(body))
                self._send(200, openai_to_anthropic(resp, model))
            else:                                                        # OpenAI chat
                self._send(200, handle_openai_chat(body))
        except Exception as e:
            self._send(502, {"error": {"message": str(e)}})


if __name__ == "__main__":
    print(f"  Agent Gateway on :{PORT} -> {UPSTREAM}  (OpenAI /v1 + Anthropic /v1/messages, defaults+tools)", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
