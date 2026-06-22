#!/usr/bin/env python3
"""Generate callsieve-first agentic tool-use trajectories for the heal, grounded
in REAL `callsieve` packets (zero-token retrieval). This bakes the token-saving
workflow INTO the model (complements wiring `callsieve mcp` at serve time): the
model learns to reach for CallSieve instead of grepping, and to consume the
compact `read_first` packet.

  python scripts/28_callsieve_protocol.py --out heal/mine/callsieve_protocol.jsonl
"""
import argparse
import json
import os
import random
import shutil
import subprocess

random.seed(0)
# Portable: env override -> callsieve on PATH -> standard install location.
CS = (os.environ.get("CALLSIEVE_BIN") or shutil.which("callsieve")
      or os.path.expanduser("~/.local/bin/callsieve"))
# Repos to mine real packets from come from --repo (default: $CS_REPOS or cwd).
# Avoid repos with huge unignored dirs (models/, .venv): agent-context slows to ~15s/call.

POLICY = ("You are an agentic coding assistant equipped with CallSieve, a local "
          "zero-token codebase retrieval tool (retrieval_model_tokens=0). For ANY "
          "task in a repository, FIRST query CallSieve for the relevant context "
          "(read_first files, symbols, call paths, tests) instead of grepping, "
          "ripgrep, scanning the tree, or reading files blindly. Read only the "
          "returned files; fall back to grep only if the packet is insufficient, "
          "and note why. Keep context compact.")

# Realistic coding tasks (parametrized by a real symbol when available).
TASK_TMPL = [
    "Add input validation to {sym}",
    "Write unit tests for {sym}",
    "Refactor {sym} to return a Result/typed error instead of panicking",
    "Find everywhere {sym} is called and add structured logging",
    "Fix the edge-case bug in {sym}",
    "Add rate limiting around {sym}",
    "Document {sym} and its callers",
    "Reduce allocations in {sym}",
    "Add a regression test that covers {sym}",
    "Trace the call path into {sym} and explain the blast radius",
]
GENERIC = [
    "Where is auth/session handling and how do I extend it?",
    "Add a new subcommand to the CLI",
    "Wire a new MCP tool end to end",
    "Find the slowest path in indexing and speed it up",
    "Add a config flag and thread it through",
]


def run_cs(args, timeout=60):
    try:
        return subprocess.run([CS, *args], capture_output=True, text=True,
                              timeout=timeout).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def symbols(repo, n):
    """Pull real symbol names from a broad context packet."""
    out = run_cs(["agent-context", repo, "overview of the main modules and symbols",
                  "--format", "json"])
    syms = []
    try:
        d = json.loads(out)
        for rf in d.get("context", {}).get("read_first", []):
            for s in rf.get("sy", []):
                if isinstance(s, list) and s and isinstance(s[0], str):
                    syms.append(s[0])
    except Exception:  # noqa: BLE001
        pass
    random.shuffle(syms)
    return syms[:n] or ["main"]


def packet(repo, task):
    out = run_cs(["agent-context", repo, task, "--format", "json"])
    if not out:
        return None
    try:
        d = json.loads(out)
    except Exception:  # noqa: BLE001
        return None
    rf = [x.get("f") for x in d.get("context", {}).get("read_first", []) if x.get("f")]
    return (d, rf[:5]) if rf else None


def context_traj(repo, lang, task):
    """agent-context form: decide -> call callsieve -> read packet -> act."""
    p = packet(repo, task)
    if not p:
        return None
    d, rf = p
    name = os.path.basename(repo)
    a1 = ("Rather than grep the repo, I'll query CallSieve for the relevant context "
          f"(zero model tokens).\n\n```bash\ncallsieve agent-context . \"{task}\"\n```")
    tool = ("CallSieve packet (retrieval_model_tokens=0):\n```json\n"
            f"{json.dumps(d, separators=(',', ':'))[:1400]}\n```")
    a2 = (f"CallSieve selected read_first: {', '.join(rf)} at zero retrieval cost. "
          f"I'll open those {len(rf)} file(s) instead of grepping the {name} tree, "
          f"starting with `{rf[0]}`, then make the change there. If they don't fully "
          "cover it I'll grep narrowly and record why.")
    return {"messages": [
        {"role": "system", "content": POLICY},
        {"role": "user", "content": f"Repo `{name}` ({lang}). Task: {task}"},
        {"role": "assistant", "content": a1},
        {"role": "user", "content": tool},
        {"role": "assistant", "content": a2}]}


def symbol_traj(repo, lang, sym):
    """MCP-tool form: targeted callsieve_symbol lookup."""
    out = run_cs(["symbol", repo, sym])
    if not out:
        return None
    try:
        d = json.loads(out)
        m = (d.get("matches") or [{}])[0]
        loc = f"{m.get('file')}:{m.get('lines')}"
    except Exception:  # noqa: BLE001
        loc = "the indexed location"
    name = os.path.basename(repo)
    return {"messages": [
        {"role": "system", "content": POLICY},
        {"role": "user", "content": f"In repo `{name}` ({lang}), where is `{sym}` "
                                    "defined and what calls it?"},
        {"role": "assistant", "content":
            "I'll use CallSieve's symbol tool (zero tokens) rather than grep.\n\n"
            f"```\ncallsieve_symbol({sym})\n```"},
        {"role": "user", "content": f"```json\n{out[:1200]}\n```"},
        {"role": "assistant", "content":
            f"`{sym}` is at {loc}. CallSieve gives the signature, imports, and "
            "callers directly, so I avoid a tree-wide grep and only read that span."}]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="heal/mine/callsieve_protocol.jsonl")
    ap.add_argument("--per-repo", type=int, default=120)
    ap.add_argument("--repo", nargs="+", default=None,
                    help="repo path(s) to mine real packets from "
                         "(default: $CS_REPOS, else current dir)")
    args = ap.parse_args()
    repos = args.repo or [p for p in
                          os.environ.get("CS_REPOS", os.getcwd()).split(os.pathsep) if p]
    rows = []
    for repo in repos:
        repo = os.path.abspath(os.path.expanduser(repo))
        lang = "code"
        if not os.path.isdir(repo):
            print(f"  [skip] {repo} missing")
            continue
        run_cs(["index", repo])
        syms = symbols(repo, args.per_repo)
        tasks = [t.format(sym=random.choice(syms)) for t in TASK_TMPL
                 for _ in range(max(1, args.per_repo // (2 * len(TASK_TMPL))))]
        tasks += GENERIC
        random.shuffle(tasks)
        got = 0
        for task in tasks[:args.per_repo]:
            tr = context_traj(repo, lang, task)
            if tr:
                rows.append(tr)
                got += 1
        for sym in syms[:args.per_repo // 3]:
            tr = symbol_traj(repo, lang, sym)
            if tr:
                rows.append(tr)
                got += 1
        print(f"  {os.path.basename(repo)} ({lang}): {got} trajectories")
    random.shuffle(rows)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        f.write("\n".join(json.dumps(r) for r in rows))
    print(f"  wrote {len(rows)} callsieve-protocol trajectories -> {args.out}")


if __name__ == "__main__":
    main()
