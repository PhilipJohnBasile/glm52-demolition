#!/usr/bin/env python3
"""Overnight head-to-head (#111) — our agent/souls vs cloud agents (+ local MLX) fixing injected callsieve bugs.
CRASH-SAFE: cloud agents are memory-light; OUR model is served via serve_stable (MLX_MEM_GB) ONE soul at a time,
never alongside another big model; a memory watchdog gates every local-model load. Each contestant runs in its own
throwaway `git worktree` of callsieve (reset between) so they can't corrupt the repo or each other. Scoring =
`cargo test` EXIT CODE (bulletproof). Runs until --stop. Appends HEADTOHEAD.jsonl + prints a leaderboard.

  python scripts/headtohead.py --stop 07:00 --cloud-only          # cloud agents only (no GPU)
  python scripts/headtohead.py --stop 07:00 --souls soul2,security # add our souls (needs the GPU free)
"""
import argparse, json, os, random, re, shutil, subprocess as sp, time
from datetime import datetime, timedelta

CS = os.environ.get("CALLSIEVE_REPO", os.path.expanduser("~/git/callsieve"))  # target repo to mutate
GLM = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))          # this repo (scripts/..)
RESULTS = os.path.join(GLM, "HEADTOHEAD.jsonl")
PORT = 8080
random.seed()

# (find, replace) operator mutations a unit test will catch
MUTS = [(".div_ceil(4)", " / 4"), (".div_ceil(2)", " / 2"), (" + 1", " + 2"), (" - 1", " + 1"),
        (" >= ", " > "), (" <= ", " < "), (" == ", " != "), (".saturating_sub(1)", ".saturating_sub(2)"),
        (" > ", " < "), (" < ", " > ")]
SRCS = ["src/query/tokens.rs", "src/query/classify.rs", "src/query/skeleton.rs"]  # focused files (dropped 1700-line mcp.rs collapse-trap)
# cloud contestants: name -> argv (runner takes task+worktree; cloud runs in the worktree cwd)
CLOUD = {
    "claude": lambda t, wt: ["claude", "-p", t, "--dangerously-skip-permissions"],
    "codex":  lambda t, wt: ["codex", "exec", t],
    "agy":    lambda t, wt: ["agy", "-p", t, "--dangerously-skip-permissions", "--add-dir", "."],
}
# OUR local corner: 57-tool ReAct agent vs serve_stable on :PORT (one soul resident at a time)
def ours_runner(t, wt):
    return [".venv/bin/python", "-u", "scripts/57_tool_agent.py", "--repo", wt, "--task", t,
            "--test", "cargo test", "--apply", "--max-steps", "15", "--base-url", f"http://localhost:{PORT}/v1"]


def sh(cmd, cwd=None, timeout=None, env=None):
    try:
        return sp.run(cmd, cwd=cwd, timeout=timeout, capture_output=True, text=True, env=env)
    except Exception:
        return None


def free_pct():
    r = sh(["memory_pressure"])
    if not r:
        return 0
    for line in r.stdout.splitlines():
        if "free perc" in line.lower():
            import re
            m = re.search(r"(\d+)%", line)
            return int(m.group(1)) if m else 0
    return 0


def mk_worktree(tag):
    wt = f"/tmp/h2h_{tag}_{int(time.time()*1000)%100000}"
    sh(["git", "-C", CS, "worktree", "remove", "--force", wt])
    shutil.rmtree(wt, ignore_errors=True)
    sh(["git", "-C", CS, "worktree", "add", "-f", wt, "HEAD"])
    return wt


def rm_worktree(wt):
    sh(["git", "-C", CS, "worktree", "remove", "--force", wt])
    shutil.rmtree(wt, ignore_errors=True)


def gen_bug():
    """Pick a file+mutation that still COMPILES but breaks a test. Returns (file, find, replace) or None."""
    for _ in range(25):
        f = random.choice(SRCS)
        find, repl = random.choice(MUTS)
        wt = mk_worktree("gen")
        path = os.path.join(wt, f)
        try:
            txt = open(path).read()
        except Exception:
            rm_worktree(wt); continue
        if find not in txt:
            rm_worktree(wt); continue
        open(path, "w").write(txt.replace(find, repl, 1))
        comp = sh(["cargo", "test", "--no-run", "-q"], cwd=wt, timeout=300)
        if not comp or comp.returncode != 0:
            rm_worktree(wt); continue                     # mutation didn't compile -> skip
        test = sh(["cargo", "test", "-q"], cwd=wt, timeout=600)
        rm_worktree(wt)
        if test and test.returncode != 0:                 # a test broke -> a real, caught bug
            return f, find, repl
    return None


def run_contestant(name, runner, bug):
    """Fresh worktree -> inject bug -> run contestant -> cargo test exit code. Returns dict result."""
    f, find, repl = bug
    wt = mk_worktree(name)
    path = os.path.join(wt, f)
    open(path, "w").write(open(path).read().replace(find, repl, 1))
    is_ours = name.startswith("ours")
    armed = "armed" in name                                # A/B: ours-armed gets callsieve; ours-bare does not
    task = (f"A unit test in {f} is failing because of a bug. Find and fix ONLY the bug in the source "
            f"(do not modify any test). Then ensure `cargo test` passes.")
    if armed:
        # OURS-ARMED (v2, the PRODUCT path): callsieve localizes the bug via working-tree-diff -> the
        # CHANGED line -> route through the VALIDATED best-of-N verifier-gated fixer (bestofn_fix.py).
        # This BYPASSES the 3-bit model's read/peek/clarify gather-loops and lets `cargo test` pick the
        # right candidate (disclosable bug in 1, subtle >/< in ~3 via auto test-assertion extraction).
        # callsieve's diff localization == `git diff -U0 HEAD` here (mutation is uncommitted).
        diff = sh(["git", "-C", wt, "diff", "-U0", "HEAD", "--", f], timeout=60)
        line = None
        if diff and diff.stdout:
            m = re.search(r"@@ -\d+(?:,\d+)? \+(\d+)", diff.stdout)
            if m:
                line = int(m.group(1))
        if line:                                               # localized -> best-of-N; else fall through to agent
            t0 = time.time()
            sh([".venv/bin/python", "scripts/bestofn_fix.py", "--repo", wt, "--file", f,
                "--line", str(line), "--n", "5", "--base-url", f"http://localhost:{PORT}/v1"],
               cwd=GLM, timeout=1500)
            dt = round(time.time() - t0, 1)
            score = sh(["cargo", "test", "-q"], cwd=wt, timeout=600)
            passed = bool(score and score.returncode == 0)
            rm_worktree(wt)
            return {"contestant": name, "file": f, "mut": f"{find}->{repl}", "passed": passed,
                    "secs": dt, "private": name not in CLOUD, "mode": "bestofn",
                    "ts": datetime.now().isoformat(timespec="seconds")}
    if not is_ours:
        # cloud / other-local: deny OUR callsieve tool — strip its hooks from their copy of the repo
        for h in ("CLAUDE.md", ".mcp.json", "mcp-server.json"):
            try: os.remove(os.path.join(wt, h))
            except OSError: pass
    elif armed:
        # OURS-ARMED: callsieve v0.5.0 localizes the SOURCE bug -> short snippet (~7 lines, NOT a
        # dump: long context collapses the 3-bit model). A bug-intent query triggers callsieve's
        # working-tree-diff localization, which focuses the CHANGED source fn (the mutation is
        # uncommitted in this worktree), so it pinpoints regardless of which test caught it.
        cs = sh(["callsieve", "agent-context", wt,
                 f"a unit test in {f} is failing because of a bug; fix the source"], timeout=120)
        if cs and cs.returncode == 0 and cs.stdout.strip():
            try:
                ctx = json.loads(cs.stdout)
                pick = None
                for e in ctx.get("context", {}).get("read_first", []):
                    if e.get("f") != f:                                  # must be the buggy file
                        continue
                    for s in (e.get("sy") or []):
                        is_mod = len(s) > 2 and s[2] == "mod"
                        is_test = "test" in str(s[0]).lower()
                        if len(s) > 1 and not is_mod and not is_test:     # a real source symbol
                            pick = s[1]; break
                    if pick: break
                if pick:
                    lines = open(os.path.join(wt, f)).read().splitlines()
                    snip = "\n".join(lines[max(0, pick - 1):pick + 6])
                    # fix-packet: snippet + the failing test names (their names describe the EXPECTED
                    # behavior) + a hard directive to act now. Turns a wandering low-bit model decisive
                    # — proven: apply_patch on step 1 vs an 8-step gather-loop with the soft hint.
                    tout = sh(["cargo", "test"], cwd=wt, timeout=300)
                    blob = ((tout.stdout or "") + (tout.stderr or "")) if tout else ""
                    fails = ", ".join(re.findall(r"([A-Za-z0-9_:]+) \.\.\. FAILED", blob)[:4]) or "(run cargo test)"
                    task = (f"CallSieve fix-packet for {f}:\nBuggy function at line {pick}:\n"
                            f"```rust\n{snip}\n```\n"
                            f"Failing test(s): {fails}  (the test name describes the expected behavior).\n"
                            f"The bug is on line {pick}. Do NOT search, grep, peek, or read further — you "
                            f"already have the exact code and the test. Call apply_patch on {f} NOW to make "
                            f"the test pass, then run cargo test.")
            except Exception:
                pass
    # OURS-BARE: model + 57-agent scaffold alone (no callsieve) — the A/B control
    t0 = time.time()
    argv = runner(task, wt)
    cwd = GLM if is_ours else wt                            # ours runs 57_agent from GLM with --repo wt
    env = None
    if not is_ours:                                         # HARD-deny OUR callsieve binary to cloud/local
        env = dict(os.environ)                             # shim dir first on PATH -> `callsieve` = not found
        env["PATH"] = "/tmp/nocallsieve:" + env.get("PATH", "")
    proc = sh(argv, cwd=cwd, timeout=1500, env=env)        # 25 min cap (ours ~11 tok/s; fix-packet = fewer steps)
    dt = round(time.time() - t0, 1)
    score = sh(["cargo", "test", "-q"], cwd=wt, timeout=600)
    passed = bool(score and score.returncode == 0)
    rm_worktree(wt)
    return {"contestant": name, "file": f, "mut": f"{find}->{repl}", "passed": passed,
            "secs": dt, "private": name not in CLOUD, "ts": datetime.now().isoformat(timespec="seconds")}


def ensure_deny_shim():
    """Self-create the callsieve deny-shim so cloud/local rivals can't use OUR tool — don't rely on a
    pre-existing /tmp file (a reboot wipes it → the A/B would silently become INVALID for cloud)."""
    d = "/tmp/nocallsieve"
    os.makedirs(d, exist_ok=True)
    shim = os.path.join(d, "callsieve")
    with open(shim, "w") as w:
        w.write("#!/bin/sh\necho 'callsieve: not available' >&2\nexit 127\n")
    os.chmod(shim, 0o755)


def main():
    ensure_deny_shim()
    ap = argparse.ArgumentParser()
    ap.add_argument("--stop", default="07:00")
    ap.add_argument("--cloud-only", action="store_true")
    ap.add_argument("--souls", default="")                # comma list, needs serve_stable up + GPU
    ap.add_argument("--ours-soul", default="")            # ours mode: 57_agent vs serve_stable on :PORT
    ap.add_argument("--max-tasks", type=int, default=999)
    a = ap.parse_args()
    if a.ours_soul:
        # A/B every round: ours WITH callsieve vs ours WITHOUT (same bug) -> measure callsieve's net effect
        contestants = [f"ours-armed-{a.ours_soul}", f"ours-bare-{a.ours_soul}"]
        runners = {c: ours_runner for c in contestants}
    else:
        contestants = list(CLOUD.keys()); runners = dict(CLOUD)
    souls = []
    hh, mm = map(int, a.stop.split(":"))
    _now = datetime.now()
    stop_dt = _now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if stop_dt <= _now:
        stop_dt += timedelta(days=1)                      # crosses midnight -> tomorrow
    print(f"  head-to-head: cloud={contestants} souls={souls} stop={stop_dt:%Y-%m-%d %H:%M}", flush=True)
    n = 0
    while datetime.now() < stop_dt and n < a.max_tasks:
        bug = gen_bug()
        if not bug:
            print("  (no valid mutation this round)", flush=True); continue
        n += 1
        print(f"  [task {n}] bug={bug[0]} {bug[1]}->{bug[2]}", flush=True)
        for name in contestants:
            res = run_contestant(name, runners[name], bug)
            with open(RESULTS, "a") as w:
                w.write(json.dumps(res) + "\n")
            print(f"    {name:8} {'PASS' if res['passed'] else 'fail'} {res['secs']}s", flush=True)
        # souls go here (serve_stable per soul + 57_tool_agent) — gated by free_pct() watchdog
    # leaderboard
    rows = [json.loads(x) for x in open(RESULTS)] if os.path.exists(RESULTS) else []
    print("\n  === LEADERBOARD (pass-rate) ===", flush=True)
    for c in sorted(set(r["contestant"] for r in rows)):
        cr = [r for r in rows if r["contestant"] == c]
        p = sum(r["passed"] for r in cr)
        print(f"    {c:8} {p}/{len(cr)} = {100*p//max(1,len(cr))}%  ·  "
              f"avg {sum(r['secs'] for r in cr)/max(1,len(cr)):.0f}s  ·  "
              f"{'PRIVATE/$0' if c not in CLOUD else 'cloud/billed'}", flush=True)


if __name__ == "__main__":
    main()
