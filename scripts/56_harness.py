#!/usr/bin/env python3
"""① The agentic harness — the PRODUCT: the model that ACTS. Given a task + a repo, it
pulls context (project memory + verified-solution cache, 55), writes/edits real FILES,
runs the project's TEST command, reads the real output, and iterates until green — then
banks the verified solution so it compounds. This is "local Claude Code": private,
correct-by-construction, unlimited, and learning your repo. A cloud model can't edit
your files and run your tests in your env; this does.

Safety: DRY-RUN by default (shows the diff); pass --apply to actually write files.

  python scripts/56_harness.py --repo . --test "python -m pytest -q test_x.py" \
      --task "add a debounce() to utils.ts with correct types" --apply --budget 6
  python scripts/56_harness.py --selftest        # GPU-free, in a temp repo
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from memory import ProjectMemory, SolutionCache  # noqa: E402

FILE_RE = re.compile(r"FILE:\s*(\S+)\s*```[a-zA-Z0-9]*\n(.*?)```", re.S)
SYS = ("You are an agent editing a real repo. For each file to create or replace, emit a "
       "block exactly:\nFILE: <relative/path>\n```<lang>\n<full file contents>\n```\n"
       "Emit only such blocks, no prose.")


def chat(base_url, model, messages, temp=0.0, max_tokens=2000):
    body = json.dumps({"model": model, "messages": messages, "temperature": temp,
                       "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(base_url + "/chat/completions", body,
                                 {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=400).read())["choices"][0]["message"]["content"]


def parse_files(text):
    return [(p.strip(), c) for p, c in FILE_RE.findall(text)]


def apply_files(repo, files, apply, log=print):
    for path, content in files:
        dst = os.path.join(repo, path)
        old = open(dst).read() if os.path.exists(dst) else ""
        verb = "WRITE" if apply else "would write"
        log(f"    {verb} {path}  ({len(old)}→{len(content)} bytes)")
        if apply:
            os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
            open(dst, "w").write(content)


def run_test(repo, cmd, timeout=120):
    # PYTHONDONTWRITEBYTECODE: edited files are re-run within the same second at the
    # same byte size; Python's mtime+size .pyc check would otherwise import stale bytecode.
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        p = subprocess.run(cmd, cwd=repo, shell=True, capture_output=True, text=True,
                           timeout=timeout, env=env)
        return p.returncode == 0, (p.stdout + p.stderr)[-2500:]
    except subprocess.TimeoutExpired:
        return False, "test timeout"


def harness_solve(propose, repo, task, test_cmd, *, budget=6, apply=False, log=print,
                  cache=None, memory=None):
    """Agentic file-editing loop against the real test command. propose(task, ctx,
    diag, prev_files) -> model text with FILE: blocks."""
    ctx = ""
    if memory:
        ctx += memory.recall(task)
    if cache:
        ctx += cache.hint(task, "")
    diag, prev = "", ""
    trace = {"task": task, "iters": 0, "solved": False}
    for it in range(budget):
        text = propose(task, ctx, diag, prev, 0.0 if it == 0 else 0.4)
        files = parse_files(text)
        if not files:
            log(f"  iter {it}: no FILE blocks emitted")
            break
        apply_files(repo, files, apply, log)
        if not apply:                                    # dry-run: can't run tests on unwritten files
            log("  (dry-run — pass --apply to write + run tests)")
            trace["iters"] = it + 1
            return text, trace
        ok, out = run_test(repo, test_cmd)
        trace["iters"] = it + 1
        log(f"  iter {it}: tests {'PASS ✅' if ok else 'FAIL'}"
            + ("" if ok else f"   ↳ {out.strip().splitlines()[-1][:80] if out.strip() else ''}"))
        if ok:
            trace["solved"] = True
            if cache:
                for p, c in files:
                    cache.store(f"{task} :: {p}", "", c)   # bank the verified solution
            return text, trace
        prev, diag = text, out
    return None, trace


def selftest():
    """GPU-free: a temp repo with a real pytest; stub agent writes a buggy module first,
    reads the failing test output, then fixes it — proving file-edit + test + repair."""
    import tempfile
    repo = tempfile.mkdtemp()
    st = {"n": 0}

    def propose(task, ctx, diag, prev, temp):
        st["n"] += 1
        body = "def add(a,b):\n    return a+b" if diag else "def add(a,b):\n    return a-b"
        return f"FILE: sol.py\n```python\n{body}\n```"

    cache = SolutionCache(os.path.join(repo, "cache.jsonl"))
    test_cmd = f'{sys.executable} -c "from sol import add; assert add(2,3)==5 and add(-1,1)==0"'
    sol, trace = harness_solve(propose, repo, "implement add(a,b)", test_cmd,
                               budget=4, apply=True, cache=cache)
    banked = len(cache.items) >= 1
    ok = trace["solved"] and trace["iters"] == 2 and banked
    print(f"  selftest: solved={trace['solved']} in {trace['iters']} iters (wrote file, ran "
          f"pytest, repaired from real failure), banked={banked}  {'PASS ✅' if ok else 'FAIL'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--task", default="")
    ap.add_argument("--test", default=f"{sys.executable} -m pytest -q")
    ap.add_argument("--budget", type=int, default=6)
    ap.add_argument("--apply", action="store_true", help="actually write files (default: dry-run)")
    args = ap.parse_args()
    if args.selftest:
        raise SystemExit(0 if selftest() else 1)
    cache, memory = SolutionCache(), ProjectMemory()

    def propose(task, ctx, diag, prev, temp):
        if diag:
            user = (f"Task: {task}{ctx}\n\nYour files failed the tests:\n{diag}\n\n"
                    "Fix the root cause. Re-emit the full corrected FILE blocks.")
        else:
            user = f"Task: {task}{ctx}\n\nImplement it. Emit FILE blocks only."
        return chat(args.base_url, args.model,
                    [{"role": "system", "content": SYS}, {"role": "user", "content": user}], temp)

    sol, trace = harness_solve(propose, args.repo, args.task, args.test,
                               budget=args.budget, apply=args.apply, cache=cache, memory=memory)
    print(f"\n  {'✅ SOLVED + banked' if trace['solved'] else '⚠️ not solved'} in {trace['iters']} iters"
          + ("" if args.apply else "  (dry-run)"))


if __name__ == "__main__":
    main()
