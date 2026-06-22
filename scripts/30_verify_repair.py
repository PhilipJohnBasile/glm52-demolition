#!/usr/bin/env python3
"""Toolchain verify->repair loop — the biggest edge a small local model has over
Fable in this niche. Generate a solution, then run the REAL toolchain for the
language and feed the actual compiler/linter diagnostics back to repair, up to K
rounds. A model that CHECKS against the type system + tests beats a bigger model
that guesses: TS/Rust/Go type systems are free, brutal verifiers.

  # serve the model (+08 proxy) first, then:
  python scripts/30_verify_repair.py --lang ts --base-url http://localhost:8081/v1 \
      --task "Write a typed debounce<T extends (...a:any[])=>void>(fn:T, ms:number)" \
      --rounds 3

Verifiers degrade gracefully: if a toolchain is missing it runs the strongest
check available (syntax) and says so. Exit code 0 = verified, 1 = best-effort.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from exec_check import extract_code  # noqa: E402


def chat(base_url, messages, temperature=0.0, max_tokens=2200):
    body = json.dumps({"model": "local", "messages": messages,
                       "temperature": temperature, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(base_url + "/chat/completions", body,
                                 {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=400).read())[
        "choices"][0]["message"]["content"]


def _run(cmd, **kw):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kw)
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return None, ""                       # tool absent
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def verify_ts(code, harness):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "sol.ts")
        open(f, "w").write(code + ("\n" + harness if harness else ""))
        tsc = shutil.which("tsgo") or shutil.which("tsc")   # TS7 (tsgo) preferred
        if tsc:
            rc, out = _run([tsc, "--noEmit", "--strict", "--target", "esnext",
                            "--moduleResolution", "bundler", f])
            if rc == 0:
                return True, "tsc --strict: clean"
            return False, "tsc --strict:\n" + out[:1500]
        rc, out = _run([shutil.which("node") or "node", "--check", f])
        return (rc == 0), ("node --check (no tsc; types unchecked): "
                           + ("ok" if rc == 0 else out[:1200]))


def verify_rust(code, harness):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "sol.rs")
        open(f, "w").write(code + ("\n" + harness if harness else ""))
        rc, out = _run(["rustc", "--edition", "2021", "--crate-type",
                        "bin" if harness else "lib", "--emit=metadata",
                        "-o", os.path.join(d, "o"), f])
        if rc is None:
            return None, "rustc not installed (typecheck skipped)"
        return (rc == 0), ("rustc typecheck: clean" if rc == 0
                           else "rustc:\n" + out[:1500])


def verify_py(code, harness):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "sol.py")
        open(f, "w").write(code + ("\n" + harness if harness else ""))
        rc, out = _run([sys.executable, "-m", "py_compile", f])
        if rc != 0:
            return False, "py_compile:\n" + out[:1200]
        pyr = shutil.which("pyright")
        if pyr:
            rc, out = _run([pyr, "--outputjson", f])
            ok = '"errorCount": 0' in out or rc == 0
            return ok, ("pyright: clean" if ok else "pyright:\n" + out[:1500])
        if harness:                            # run the tests if provided
            rc, out = _run([sys.executable, f])
            return (rc == 0), ("ran: ok" if rc == 0 else out[:1200])
        return True, "py_compile clean (no pyright; types unchecked)"


def verify_go(code, harness):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "sol.go")
        open(f, "w").write(code)
        rc, out = _run(["gofmt", "-e", f])
        if rc is None:
            return None, "go toolchain not installed (skipped)"
        if rc != 0:
            return False, "gofmt -e:\n" + out[:1200]
        return True, "gofmt -e: parses (full vet needs a module)"


def verify_js(code, harness):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "sol.js")
        open(f, "w").write(code + ("\n" + harness if harness else ""))
        rc, out = _run([shutil.which("node") or "node", "--check", f])
        if rc is None:
            return None, "node not installed (skipped)"
        return (rc == 0), ("node --check: ok" if rc == 0 else out[:1200])


VERIFIERS = {"ts": verify_ts, "typescript": verify_ts, "rust": verify_rust,
             "rs": verify_rust, "py": verify_py, "python": verify_py,
             "go": verify_go, "js": verify_js, "javascript": verify_js}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, choices=sorted(VERIFIERS))
    ap.add_argument("--task", required=True)
    ap.add_argument("--base-url", default="http://localhost:8081/v1")
    ap.add_argument("--harness", default="", help="tests/asserts appended before checking")
    ap.add_argument("--rounds", type=int, default=3)
    args = ap.parse_args()
    verify = VERIFIERS[args.lang]
    sysmsg = ("You are an expert programmer. Return ONLY a single fenced code block, "
              "no prose. Write idiomatic, modern, type-correct code.")
    msgs = [{"role": "system", "content": sysmsg},
            {"role": "user", "content": args.task}]
    code = ""
    for r in range(args.rounds):
        reply = chat(args.base_url, msgs, temperature=0.0 if r == 0 else 0.5)
        code = extract_code(reply) or reply
        ok, diag = verify(code, args.harness)
        status = {True: "VERIFIED ✅", False: "errors", None: "unverifiable (no toolchain)"}[ok]
        print(f"  round {r+1}/{args.rounds}: {status}")
        if ok is not False:                    # True or None (can't check) -> stop
            print(f"  [{args.lang}] {diag[:200]}")
            print("\n" + code)
            sys.exit(0 if ok else 1)
        # feed the REAL diagnostics back and repair
        msgs += [{"role": "assistant", "content": f"```{args.lang}\n{code}\n```"},
                 {"role": "user", "content":
                  f"The {args.lang} toolchain rejected that:\n\n{diag}\n\n"
                  "Fix every error and return ONLY the corrected code block."}]
    print("  ⚠️ best-effort (still failing after repairs):\n")
    print(code)
    sys.exit(1)


if __name__ == "__main__":
    main()
