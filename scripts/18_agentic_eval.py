#!/usr/bin/env python3
"""AGENTIC eval — measures what actually matters for an agentic coding model:
tool selection, argument correctness, multi-step task completion, and NOT
over-calling tools. Single-function code quality is 07_eval.py; this is the
agent behavior that 07 doesn't capture.

Runs against an OpenAI-compatible endpoint with real `tools` in the request,
drives a mock tool environment for multi-step tasks, and scores:
  tool_select : picked the right tool with right-ish args
  no_tool     : answered directly without spuriously calling a tool
  multi_step  : reached the goal (e.g. wrote a fix then tests passed) in budget

  python scripts/18_agentic_eval.py --base-url http://localhost:8081/v1 --label agentic
"""

import argparse
import json
import os
import sys
import urllib.request
from collections import defaultdict

HERE = os.path.dirname(__file__)
TASKS = os.path.join(HERE, "..", "eval", "agentic_tasks.jsonl")

TOOL_SCHEMAS = {
    "read_file": {"path": "string"}, "write_file": {"path": "string", "content": "string"},
    "run_tests": {}, "list_dir": {"path": "string"},
}


def schema(name):
    props = {k: {"type": v} for k, v in TOOL_SCHEMAS.get(name, {}).items()}
    return {"type": "function", "function": {
        "name": name, "description": f"{name} tool",
        "parameters": {"type": "object", "properties": props}}}


def call(base_url, messages, tools):
    body = {"model": "local", "messages": messages, "temperature": 0.0,
            "max_tokens": 700, "tools": [schema(t) for t in tools]}
    req = urllib.request.Request(base_url + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]


def tool_calls(msg):
    """Normalize tool calls from either the tool_calls field or inline JSON."""
    out = []
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function", {})
        args = fn.get("arguments")
        if isinstance(args, str):
            try: args = json.loads(args)
            except Exception: args = {}
        out.append((fn.get("name"), args or {}))
    return out


def score_select(task, msg):
    tcs = tool_calls(msg)
    exp = task["expect"]
    if exp["tool"] is None:                      # no_tool: must NOT call a tool
        return len(tcs) == 0
    if not tcs:
        return False
    name, args = tcs[0]
    if name != exp["tool"]:
        return False
    for k, v in exp.get("arg_contains", {}).items():
        if v.lower() not in str(args.get(k, "")).lower():
            return False
    return True


def score_multi(task, base_url):
    msgs = [{"role": "user", "content": task["prompt"]}]
    wrote = False
    for _ in range(task["max_steps"]):
        msg = call(base_url, msgs, task["tools"])
        tcs = tool_calls(msg)
        if not tcs:
            break
        msgs.append({"role": "assistant", "content": msg.get("content") or "",
                     "tool_calls": msg.get("tool_calls")})
        for name, args in tcs:
            if name == "write_file":
                wrote = True
            # mock environment: run_tests passes only after a write
            if name == "run_tests":
                result = "All tests passed" if wrote else "FAIL: assertion error"
            else:
                result = task["mock"].get(name, "ok")
            msgs.append({"role": "tool", "content": result})
            # goal: a run_tests that passes, or read after list for investigate
            if task["goal_tool"] == "run_tests" and name == "run_tests" and wrote:
                return True
            if task["goal_tool"] == "read_file" and name == "read_file":
                return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8081/v1")
    ap.add_argument("--label", default="agentic")
    args = ap.parse_args()
    tasks = [json.loads(l) for l in open(TASKS)]
    by_type = defaultdict(lambda: [0, 0])
    for t in tasks:
        try:
            if t["type"] == "multi_step":
                ok = score_multi(t, args.base_url)
            else:
                ok = score_select(t, call(args.base_url,
                                  [{"role": "user", "content": t["prompt"]}], t["tools"]))
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] {t['id']}: {str(e)[:50]}"); ok = False
        by_type[t["type"]][0] += int(ok)
        by_type[t["type"]][1] += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {t['type']:12} {t['id']}")

    print(f"\n=== {args.label}: agentic capability ===")
    tot_p = tot_n = 0
    for ty, (p, n) in sorted(by_type.items()):
        print(f"  {ty:14} {p}/{n}")
        tot_p += p; tot_n += n
    print(f"  OVERALL agentic {tot_p}/{tot_n}")
    json.dump({k: v for k, v in by_type.items()},
              open(os.path.join(HERE, "..", "eval", f"agentic-{args.label}.json"), "w"))


if __name__ == "__main__":
    main()
