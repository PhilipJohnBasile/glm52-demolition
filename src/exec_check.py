"""Shared correctness checkers used by BOTH the eval (07) and the verified-SFT
builder (06b), so "passes" means the same thing in scoring and in training-data
selection. Execution-based where a toolchain exists; structural fallback for
HTML/CSS. Returns True (pass), False (fail), or None (skipped: no toolchain).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile


def extract_code(text: str) -> str:
    m = re.search(r"```[a-zA-Z]*\n(.*?)```", text, re.S)
    return m.group(1) if m else text


def _ok(cmd, cwd, env=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           timeout=120, env=env)
        return p.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def run_python(code: str, test_code: str) -> bool:
    """Run candidate `code` then `test_code` (asserts) in one interpreter."""
    if not shutil.which("python3"):
        return None
    with tempfile.TemporaryDirectory() as d:
        open(f"{d}/sol.py", "w").write(code + "\n\n" + test_code)
        return _ok(["python3", "sol.py"], d)


def check(task: dict, reply: str):
    kind = task["check"]
    code = extract_code(reply)
    if kind == "json_tool":
        try:
            obj = json.loads(re.search(r"\{.*\}", reply, re.S).group(0))
            return obj.get("tool") == task["expect_tool"]
        except Exception:  # noqa: BLE001
            return False
    if kind == "structural":
        low = code.lower()
        return all(s.lower() in low for s in task["must_contain"])
    with tempfile.TemporaryDirectory() as d:
        if kind == "exec":
            if not shutil.which("python3"):
                return None
            open(f"{d}/solution.py", "w").write(code)
            open(f"{d}/t.py", "w").write(task["harness"])
            return _ok(["python3", "t.py"], d)
        if kind == "exec_node":
            if not shutil.which("node"):
                return None
            open(f"{d}/solution.js", "w").write(code)
            open(f"{d}/t.js", "w").write(task["harness"])
            return _ok(["node", "t.js"], d)
        if kind == "compile_ts":
            if not shutil.which("npx"):
                return None
            open(f"{d}/s.ts", "w").write(code)
            # 100% TypeScript 7: tsgo (Go-native, @typescript/native-preview) is
            # the authority. Fall back to tsc 6 only if tsgo can't be fetched
            # (same language, so a valid safety net) — never silently skip TS.
            try:
                p = subprocess.run(
                    ["npx", "-y", "-p", "@typescript/native-preview",
                     "tsgo", "--noEmit", "--strict", "s.ts"],
                    cwd=d, capture_output=True, text=True, timeout=120)
                if "could not determine executable" not in (p.stderr or "") \
                        and "npm error" not in (p.stderr or ""):
                    return p.returncode == 0           # tsgo (TS7) verdict
            except Exception:  # noqa: BLE001
                pass
            return _ok(["npx", "-y", "typescript@6", "tsc", "--noEmit",
                        "--strict", "s.ts"], d)            # fallback only
        if kind == "compile_rust":
            if not shutil.which("rustc"):
                return None
            open(f"{d}/s.rs", "w").write(code + "\n" + task["harness"])
            return _ok(["rustc", "-o", "s", "s.rs"], d) and _ok(["./s"], d)
        if kind == "compile_go":
            if not shutil.which("go"):
                return None
            os.makedirs(f"{d}/solution", exist_ok=True)
            open(f"{d}/solution/s.go", "w").write(code)
            open(f"{d}/solution/s_test.go", "w").write(task["harness"])
            open(f"{d}/go.mod", "w").write("module eval\ngo 1.21\n")
            env = dict(os.environ, GOFLAGS="-mod=mod", GO111MODULE="on")
            return _ok(["go", "test", "./solution/"], d, env=env)
    return None
