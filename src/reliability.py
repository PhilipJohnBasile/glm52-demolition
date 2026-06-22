"""Reliability layer — keeps the agent trustworthy as tasks get LONG and codebases get BIG.
The 2026 production gaps (with hard numbers) that frontier agents degrade on by default:
 1. context rot — constraint compliance drops 73%@turn5 -> 33%@turn16. Fix: pin constraints +
    rolling summary so the task's hard rules never fall out of attention.
 2. silent false-success — agents "succeed" when the tool errored. Fix: verify_success.
 3. flaky tests — agents chase non-deterministic failures forever. Fix: flaky_check (re-run N).
 4. re-onboarding every trajectory — agents re-derive the codebase each task. Fix: onboard() map.
"""
import json
import os
import re
import subprocess
import time
from collections import Counter

# ---- 1. context-rot defense: constraint pinning + rolling summary ----------------------
_CON = [r"must(?:n'?t| not)?\b", r"should(?:n'?t| not)?\b", r"do(?:n'?t| not)\b", r"\bensure\b",
        r"\balways\b", r"\bnever\b", r"\brequires?\b", r"\bkeep\b", r"\bonly\b", r"\bavoid\b"]


def pin_constraints(task):
    """Extract the HARD constraints from a task so they can be re-pinned every turn (anti-rot)."""
    out = []
    for line in re.split(r"[.\n;]", task or ""):
        s = line.strip()
        if 4 < len(s) < 200 and any(re.search(p, s, re.I) for p in _CON):
            out.append(s)
    return out[:8]


def rolling_summary(messages, keep=6):
    """Compress an over-long transcript: keep the system + first user + last `keep`; digest the
    middle into bullets (actions taken) so older context/constraints don't silently fall off."""
    if len(messages) <= keep + 2:
        return messages
    head, mid, tail = messages[:2], messages[2:-keep], messages[-keep:]
    acts = [m.get("content", "")[:90] for m in mid if m.get("role") == "assistant"]
    digest = {"role": "user", "content": "[earlier steps — digest]\n" + "\n".join(f"· {a}" for a in acts[:14])}
    return head + [digest] + tail


# ---- 2. false-success / uncertainty guard ----------------------------------------------
_BAD = ["error", "exception", "traceback", "failed", "cannot", "not found",
        "no such", "blocked", "refused", "denied", "panic", "fatal", "unresolved", "undefined"]


def verify_success(tool, result):
    """Catch silent false-success: the tool 'returned' but the evidence says it didn't work."""
    import re
    s = str(result).lower()
    hits = [b for b in _BAD if b in s]
    if re.search(r"\bexit=[1-9]\d*\b", s):               # ANY non-zero exit (precise; old 'exit=1'/'exit=2' substrings missed exit=3..9/127)
        hits.append("nonzero-exit")
    return (f"⚠️ {tool} may NOT have succeeded (evidence: {hits[:3]}) — verify before claiming done"
            if hits else "")


# ---- 3. flaky-test handling ------------------------------------------------------------
def flaky_check(cmd, repo=".", n=3, timeout=180):
    """Run a test command N times; separate FLAKY (non-deterministic) from a real failure."""
    res = []
    for _ in range(n):
        try:
            p = subprocess.run(cmd, cwd=repo, shell=True, capture_output=True, text=True, timeout=timeout)
            res.append(p.returncode == 0)
        except Exception:  # noqa: BLE001
            res.append(False)
    if all(res):
        return f"deterministic PASS ({n}/{n})"
    if not any(res):
        return f"deterministic FAIL ({0}/{n}) — a REAL failure, fix it"
    return f"⚠️ FLAKY: {sum(res)}/{n} passed — non-deterministic; do NOT chase as a real bug"


# ---- 4. codebase onboarding map (persist; don't re-derive every trajectory) ------------
_SKIP = {".git", "node_modules", "target", "dist", "build", ".venv", "__pycache__", ".next"}
_ENTRY = {"main.rs", "lib.rs", "mod.rs", "main.go", "index.ts", "index.js", "main.py",
          "__main__.py", "app.py", "server.py", "cli.py"}
_CONF = {"Cargo.toml", "package.json", "go.mod", "pyproject.toml", "requirements.txt",
         "Makefile", "tsconfig.json", "docker-compose.yml"}


def onboard(repo, refresh=False):
    """Generate + cache an architecture map so the agent loads it instead of re-onboarding."""
    cache = os.path.join(repo, ".agent_onboard.json")
    if os.path.exists(cache) and not refresh:
        try:
            return open(cache).read()[:3000]
        except OSError:
            pass
    langs, entries, confs, total = Counter(), [], [], 0
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in _SKIP]
        for f in files:
            total += 1
            ext = os.path.splitext(f)[1]
            if ext:
                langs[ext] += 1
            rel = os.path.relpath(os.path.join(root, f), repo)
            if f in _ENTRY:
                entries.append(rel)
            if f in _CONF:
                confs.append(rel)
    readme = ""
    for r in ("README.md", "readme.md"):
        p = os.path.join(repo, r)
        if os.path.exists(p):
            readme = open(p).read()[:400]
            break
    mp = {"files": total, "languages": dict(langs.most_common(6)), "entry_points": entries[:10],
          "configs": confs[:10], "readme_head": readme, "mapped_at": round(time.time())}
    blob = json.dumps(mp, indent=1)
    try:
        open(cache, "w").write(blob)
    except OSError:
        pass
    return blob


# ---- 5. clarify — ask before assuming (the most-praised 2026 pattern) ------------------
_VAGUE = {"it", "this", "that", "stuff", "things", "etc", "somehow", "better", "improve",
          "fix", "nice", "good", "handle", "cleanup", "clean", "optimize", "refactor", "work"}


def needs_clarification(task):
    """Heuristic: underspecified task? (short, vague, no concrete file/criterion/example)."""
    t = (task or "").strip()
    words = t.split()
    if len(words) < 5:
        return True
    vague = sum(1 for w in words if w.lower().strip(".,!?") in _VAGUE)
    concrete = bool(re.search(r"[\w/]+\.\w+|`[^`]+`|\btest\b|\bclass\b|\bfunction\b|\bfn\b|\bAPI\b|\d", t))
    return vague >= 2 and not concrete


def clarifying_questions(task):
    """The questions to ASK before acting on an ambiguous task (instead of assuming)."""
    return ["Acceptance criterion — how exactly do we know it's done / correct?",
            "Which file(s) / module(s) does this touch?",
            "Constraints to respect (perf, deps, style, backwards-compat)?",
            "An example input -> expected output?",
            "Edge cases or error behavior that matter?",
            "Should I add / run tests to verify?"]


def selftest():
    import tempfile
    repo = tempfile.mkdtemp()
    open(os.path.join(repo, "main.py"), "w").write("print(1)")
    open(os.path.join(repo, "pyproject.toml"), "w").write("[project]")
    cons = pin_constraints("You must use OKLCH colors. Never use !important. Keep it under 50 lines.")
    fs = verify_success("run", "exit=1\nTraceback ...") != "" and verify_success("run", "exit=0 ok") == ""
    fl = "FLAKY" in flaky_check("python -c \"import random,sys; sys.exit(random.randint(0,1))\"", n=4)
    mp = "main.py" in onboard(repo)
    summ = len(rolling_summary([{"role": "user", "content": str(i)} for i in range(20)])) < 20
    ok = len(cons) >= 3 and fs and mp and summ
    print(f"  reliability selftest: pin={len(cons)} false-success={fs} flaky={fl} onboard={mp} "
          f"summary={summ}  {'PASS ✅' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
