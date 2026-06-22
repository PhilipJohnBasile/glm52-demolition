#!/usr/bin/env python3
"""Agentic-code-first heal data — the flywheel. We have 49k code SNIPPETS but ~0 agentic
TRACES, so the model can generate code but isn't trained to ITERATE. This runs our own
18-tool agent (scripts/57) on coding tasks, captures the full read→edit→run-tests→read-
error→fix→done transcript (real tool calls + real observations), and saves the SUCCESSFUL
ones as training data — teaching the agentic LOOP + native tool-use at scale, on our own
tool format. Run it post-v4-base, then heal on the traces (v4.1 = the best agentic coder).

  python scripts/63_gen_agentic_traces.py --base-url http://localhost:8080/v1 --n 40 \
      --out heal/mine/agentic_traces_v4.jsonl
"""
import argparse
import importlib.util
import json
import os
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(__file__)
_spec = importlib.util.spec_from_file_location("ta", os.path.join(HERE, "57_tool_agent.py"))
ta = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ta)

# Self-contained coding tasks: (lang, file, task, test-command run in the temp repo).
TASKS = [
    ("python", "sol.py", "Write is_palindrome(s) ignoring case and non-alphanumerics.",
     'python -c "from sol import is_palindrome as f; assert f(\'A man, a plan, a canal: Panama\') and not f(\'abc\')"'),
    ("python", "sol.py", "Write merge_intervals(intervals) merging overlapping [start,end] pairs.",
     'python -c "from sol import merge_intervals as f; assert f([[1,3],[2,6],[8,10]])==[[1,6],[8,10]]"'),
    ("python", "sol.py", "Write lru_cache_get_put(): an LRUCache class with O(1) get/put, capacity 2.",
     'python -c "from sol import LRUCache; c=LRUCache(2); c.put(1,1); c.put(2,2); assert c.get(1)==1; c.put(3,3); assert c.get(2)==-1"'),
    ("python", "sol.py", "Write top_k_frequent(nums,k) returning the k most frequent elements.",
     'python -c "from sol import top_k_frequent as f; assert sorted(f([1,1,1,2,2,3],2))==[1,2]"'),
]


def make_call(base_url, model):
    def call(transcript):
        body = json.dumps({"model": model, "messages": transcript, "temperature": 0.3,
                           "max_tokens": 1200, "chat_template_kwargs": {"enable_thinking": False}}).encode()
        req = urllib.request.Request(base_url + "/chat/completions", body,
                                     {"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]["content"]
    return call


def run_one(call, lang, fname, task, test_cmd):
    """Run the agent in a temp repo; return (solved, transcript-as-training-messages)."""
    repo = tempfile.mkdtemp()
    tools = ta.make_tools(repo, test_cmd, apply=True)
    captured = []

    def call_capture(transcript):
        reply = call(transcript)
        captured.append((list(transcript), reply))
        return reply

    trace = ta.agent_loop(call_capture, tools, task, max_steps=10, log=lambda *a: None)
    if not trace["done"]:
        return False, None
    # the FULL final transcript (system+task+all tool turns) is the training example
    final = captured[-1][0] + [{"role": "assistant", "content": captured[-1][1]}]
    return True, {"messages": final, "meta": {"lang": lang, "steps": trace["steps"],
                                              "tools": trace["tools_used"]}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "heal", "mine", "agentic_traces_v4.jsonl"))
    args = ap.parse_args()
    call = make_call(args.base_url, args.model)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    saved = 0
    with open(args.out, "a") as f:
        for i in range(args.n):
            lang, fn, task, test = TASKS[i % len(TASKS)]
            try:
                ok, ex = run_one(call, lang, fn, task, test)
            except Exception as e:  # noqa: BLE001
                print(f"    task {i}: error {str(e)[:50]}")
                continue
            if ok:
                f.write(json.dumps(ex) + "\n")
                f.flush()
                saved += 1
            print(f"    task {i} [{lang}]: {'✓ trace saved' if ok else '✗ unsolved'} "
                  f"({ex['meta']['steps'] if ok else '-'} steps)", flush=True)
    print(f"\n  {saved}/{args.n} agentic traces -> {args.out}  (edit→test→fix loops, tool-use)")
    print("  next: fold into the heal corpus (62) + re-heal -> agentic-code-first v4.1")


if __name__ == "__main__":
    main()
