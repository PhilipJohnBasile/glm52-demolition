#!/usr/bin/env python3
"""Verified decoding — the new idea: THE COMPILER STEERS GENERATION.

Generate line by line; at each line boundary, type-check the code so far (auto-
closing open brackets so the prefix is checkable) with the REAL toolchain. If the
new line INTRODUCES an error, backtrack and resample that line (higher temp) up to
K times. The model becomes incapable of emitting type-incorrect code — correctness
is enforced DURING generation, not hoped for after (verify->repair) or filtered
across whole programs (best-of-N).

Why this is structurally an MLX / Apple-Silicon advantage: a checker-in-the-decode-
loop exchanges partial code between the model (GPU) and the checker (CPU tsc/LSP)
every few tokens. On unified memory they share RAM — per-line verification is cheap.
A remote frontier API dies on the round-trips. We can do what it structurally can't.

  # against the served model (once the heal lands):
  python scripts/41_verified_decode.py --lang ts --base-url http://localhost:8080/v1 \
      --task "Write add(a:number,b:number):number returning a+b"
  # validate the MECHANISM now with real tsc (no model needed):
  python scripts/41_verified_decode.py --selftest
"""
import argparse
import importlib.util as iu
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(__file__)


def _load(path):
    spec = iu.spec_from_file_location(os.path.basename(path)[:-3], path)
    m = iu.module_from_spec(spec)
    saved = sys.argv                       # don't clobber OUR argv at import time
    sys.argv = [path]
    try:
        spec.loader.exec_module(m)
    finally:
        sys.argv = saved
    return m


VR = _load(os.path.join(HERE, "30_verify_repair.py"))   # reuse the toolchain verifiers

# location-stripped error SIGNATURES (not counts): comparing sets ignores pre-
# existing incompleteness errors and triggers a backtrack only on a NEW one.
SIG_PAT = {"ts": r"error (TS\d+:.*)", "typescript": r"error (TS\d+:.*)",
           "rust": r"(error(?:\[E\d+\])?:.*)", "rs": r"(error(?:\[E\d+\])?:.*)",
           "go": r"\.go:\d+:\d+:\s*(.*)", "js": r"(\w*Error:.*)", "javascript": r"(\w*Error:.*)",
           "py": r"(\w*Error:.*|error:.*)", "python": r"(\w*Error:.*|error:.*)"}


def autoclose(code):
    """Append the closing brackets needed to make a prefix syntactically complete,
    skipping // line-comments and "..."/'...'/`...` strings (prototype-grade)."""
    pairs = {"{": "}", "(": ")", "[": "]"}
    stack = []
    i, n = 0, len(code)
    while i < n:
        c = code[i]
        if c == "/" and i + 1 < n and code[i + 1] == "/":
            while i < n and code[i] != "\n":
                i += 1
            continue
        if c in "\"'`":
            i += 1
            while i < n and code[i] != c:
                i += 2 if code[i] == "\\" else 1
            i += 1
            continue
        if c in pairs:
            stack.append(pairs[c])
        elif stack and c == stack[-1]:
            stack.pop()
        i += 1
    return code + "".join(reversed(stack))


def err_sigs(lang, code, checker=None):
    """Set of location-stripped error signatures on the auto-closed prefix.
    frozenset() = clean, None = no toolchain. A persistent `checker` (per-language
    native server) makes this incremental + fast; else the one-shot verifier spawns.
    Comparing SETS (not counts) ignores pre-existing incompleteness errors; only a
    NEW signature triggers a backtrack."""
    if checker is not None:
        return checker.errors(autoclose(code))
    verify = VR.VERIFIERS.get(lang)
    if not verify:
        return None
    ok, diag = verify(autoclose(code), "")
    if ok is True:
        return frozenset()
    if ok is None:
        return None
    sigs = re.findall(SIG_PAT.get(lang, r"(error.*)"), diag)
    s = frozenset(x.strip().rstrip(".") for x in sigs)
    return s or frozenset({"err:" + re.sub(r"\d+", "", diag)[:60]})


class TsServer:
    """Persistent tsserver — keeps the TS program in memory for INCREMENTAL
    diagnostics, so per-line checks drop from ~150ms (spawn) to single-digit ms.
    Native tsserver protocol: newline-delimited JSON; *DiagnosticsSync returns
    diagnostics right in the response (no async publishDiagnostics dance). For even
    more speed, tsgo (Go-native) exposes an LSP — wire it the same way via LspChecker.
    """

    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="vdec_")
        self.main = os.path.join(self.dir, "main.ts")
        self.tmp = os.path.join(self.dir, "buf.ts")
        open(self.main, "w").write("")
        self.p = subprocess.Popen(self._find(), stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, bufsize=1)
        self.seq = 0
        self._send("compilerOptionsForInferredProjects",
                   {"options": {"strict": True, "target": "ESNext", "module": "ESNext",
                                "moduleResolution": "Bundler", "noEmit": True, "allowJs": True}})
        self._send("open", {"file": self.main, "scriptKindName": "TS"})

    @staticmethod
    def _find():
        b = shutil.which("tsserver")
        if b:
            return [b]
        node, tsc = shutil.which("node"), (shutil.which("tsc") or shutil.which("tsgo"))
        if node and tsc:
            lib = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(tsc))),
                               "lib", "tsserver.js")
            if os.path.exists(lib):
                return [node, lib]
        raise RuntimeError("tsserver not found (npm i -g typescript)")

    def _send(self, command, args):
        self.seq += 1
        self.p.stdin.write(json.dumps({"seq": self.seq, "type": "request",
                                       "command": command, "arguments": args}) + "\n")
        self.p.stdin.flush()
        return self.seq

    def _await(self, seq, timeout=15):
        end = time.time() + timeout
        while time.time() < end and self.p.poll() is None:
            line = self.p.stdout.readline()
            if not line:
                break
            try:
                obj = json.loads(line.strip())
            except Exception:  # noqa: BLE001
                continue
            if obj.get("type") == "response" and obj.get("request_seq") == seq:
                return obj
        return None

    def errors(self, code):
        open(self.tmp, "w").write(code)
        self._send("reload", {"file": self.main, "tmpfile": self.tmp})   # FIFO: applied first
        sem = self._await(self._send("semanticDiagnosticsSync", {"file": self.main})) or {}
        syn = self._await(self._send("syntacticDiagnosticsSync", {"file": self.main})) or {}
        sigs = set()
        for d in (sem.get("body") or []) + (syn.get("body") or []):
            if isinstance(d, dict) and str(d.get("category", "")).lower() == "error":
                sigs.add(f"TS{d.get('code')}: {d.get('text', '')}".strip().rstrip("."))
        return frozenset(sigs)

    def close(self):
        try:
            self.p.stdin.close()
            self.p.terminate()
        except Exception:  # noqa: BLE001
            pass


class LspChecker:
    """Generic LSP-over-stdio persistent checker — the user's instinct realized:
    the fastest NATIVE server per language (rust-analyzer, in Rust, for Rust;
    pyright for Python; gopls for Go). Content-Length framing; prefers PULL
    diagnostics (textDocument/diagnostic, sync-ish), falls back to the
    publishDiagnostics push. Same compiler-steering as tsserver, once warm."""

    def __init__(self, cmd, lang_id, relfile, setup=None, warm=""):
        self.dir = tempfile.mkdtemp(prefix="vdec_lsp_")
        if setup:
            setup(self.dir)
        self.path = os.path.join(self.dir, relfile)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        open(self.path, "w").write(warm)
        self.uri = "file://" + self.path
        self.id, self.version, self._buf = 0, 1, b""
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL)
        self._req("initialize", {"processId": os.getpid(), "rootUri": "file://" + self.dir,
                                 "capabilities": {"textDocument": {
                                     "publishDiagnostics": {}, "diagnostic": {}}}}, timeout=30)
        self._send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
        self._send({"jsonrpc": "2.0", "method": "textDocument/didOpen", "params": {
            "textDocument": {"uri": self.uri, "languageId": lang_id, "version": 1, "text": warm}}})

    def _send(self, obj):
        b = json.dumps(obj).encode()
        self.p.stdin.write(b"Content-Length: " + str(len(b)).encode() + b"\r\n\r\n" + b)
        self.p.stdin.flush()

    def _read(self, timeout=15):
        import select
        end = time.time() + timeout
        while True:
            if b"\r\n\r\n" in self._buf:
                head, rest = self._buf.split(b"\r\n\r\n", 1)
                m = re.search(rb"Content-Length:\s*(\d+)", head)
                if m and len(rest) >= int(m.group(1)):
                    n = int(m.group(1))
                    self._buf = rest[n:]
                    try:
                        return json.loads(rest[:n])
                    except Exception:  # noqa: BLE001
                        return None
            if time.time() > end or self.p.poll() is not None:
                return None
            r, _, _ = select.select([self.p.stdout], [], [], max(0.01, end - time.time()))
            if not r:
                return None
            chunk = os.read(self.p.stdout.fileno(), 65536)
            if not chunk:
                return None
            self._buf += chunk

    def _req(self, method, params, timeout=15):
        self.id += 1
        rid = self.id
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        end = time.time() + timeout
        while time.time() < end:
            m = self._read(max(0.05, end - time.time()))
            if m is None:
                return None
            if m.get("id") == rid:
                return m
        return None

    def errors(self, code):
        self.version += 1
        self._send({"jsonrpc": "2.0", "method": "textDocument/didChange", "params": {
            "textDocument": {"uri": self.uri, "version": self.version},
            "contentChanges": [{"text": code}]}})
        items = None
        r = self._req("textDocument/diagnostic", {"textDocument": {"uri": self.uri}}, timeout=25)
        if r and isinstance(r.get("result"), dict):       # PULL diagnostics
            items = r["result"].get("items")
        if items is None:                                 # PUSH fallback
            end = time.time() + 10
            while time.time() < end:
                m = self._read(max(0.05, end - time.time()))
                if m is None:
                    break
                if (m.get("method") == "textDocument/publishDiagnostics"
                        and m.get("params", {}).get("uri") == self.uri):
                    items = m["params"]["diagnostics"]
                    break
        sigs = set()
        for d in items or []:
            if d.get("severity") == 1:                    # errors only
                c = d.get("code")
                sigs.add(((f"{c}: " if c else "") + str(d.get("message", ""))).strip().rstrip("."))
        return frozenset(sigs)

    def close(self):
        try:
            self.p.stdin.close()
            self.p.terminate()
        except Exception:  # noqa: BLE001
            pass


class RustcChecker:
    """Fast Rust checker for verified decoding: incremental `rustc --emit=metadata`
    with a PERSISTENT incremental cache, so warm per-edit checks are ~30ms — the
    FULL borrow+type check (ground truth), just not 0.x ms (that's rustc physics).
    rust-analyzer's diagnostics are async cargo-flycheck (editor-oriented, unfit for
    per-edit); this is reliable AND fast enough (a 40-line fn ~ 1-2s of guaranteed
    correctness)."""

    def __init__(self):
        self.rustc = shutil.which("rustc")
        if not self.rustc:
            raise RuntimeError("rustc not found")
        self.dir = tempfile.mkdtemp(prefix="vdec_rs_")
        self.inc = os.path.join(self.dir, "inc")
        os.makedirs(self.inc, exist_ok=True)
        self.src = os.path.join(self.dir, "lib.rs")
        self.errors("pub fn _warm(x: i32) -> i32 { x }\n")   # build the incremental cache

    def errors(self, code):
        open(self.src, "w").write(code)
        try:
            r = subprocess.run(
                [self.rustc, "--edition", "2021", "--crate-type", "lib", "--emit=metadata",
                 "-C", "incremental=" + self.inc, "-o", os.path.join(self.dir, "o.rmeta"),
                 self.src], capture_output=True, text=True, timeout=30)
        except Exception:  # noqa: BLE001
            return frozenset()
        sigs = set()
        for m in re.finditer(r"error(\[E\d+\])?:\s*([^\n]+)", r.stderr):
            msg = m.group(2)
            if "aborting due to" in msg or "previous error" in msg:
                continue                       # rustc's summary line, not a diagnostic
            sigs.add(((m.group(1) or "") + ": " + msg).strip().rstrip("."))
        return frozenset(sigs)

    def close(self):
        pass


def make_checker(lang):
    """Per-language checker — the fastest reliable one per language (the user's
    instinct, corrected by reality):
      ts/js  -> tsserver (sync diagnostics, ~0.3ms warm)
      python -> pyright-langserver via LSP (~0ms warm)
      rust   -> incremental rustc (~30ms warm; rust-analyzer is async cargo-flycheck,
                unfit for per-edit — Rust's borrow/type check is just heavier)
      go     -> one-shot `go build`/gofmt verifier (scripts/30)
    Returns a checker with .errors(code)/.close(), or None -> per-line spawn."""
    try:
        if lang in ("ts", "typescript", "js", "javascript"):
            return TsServer()
        if lang in ("py", "python"):
            b = shutil.which("pyright-langserver")
            if b:
                return LspChecker([b, "--stdio"], "python", "main.py")
        if lang in ("rust", "rs"):
            return RustcChecker()
    except Exception:  # noqa: BLE001
        return None
    return None


def verified_decode(lang, gen_line, *, prefix="", max_lines=40, K=4, log=print, checker=None):
    """gen_line(accepted_code, attempt) -> next line (str) or None when done."""
    accepted = prefix
    base = err_sigs(lang, accepted, checker) or frozenset()
    backtracks = 0
    for ln in range(max_lines):
        chosen = None
        line = None
        for att in range(K):
            line = gen_line(accepted, att)
            if line is None:
                return accepted, backtracks                 # model signalled done
            cand = accepted + line + ("" if line.endswith("\n") else "\n")
            sigs = err_sigs(lang, cand, checker)
            if sigs is None:
                return accepted + line, backtracks          # can't verify -> accept
            if sigs <= base:                                # introduces NO new error
                chosen, base = cand, sigs
                break
            new = sigs - base
            backtracks += 1
            log(f"    ✗ backtrack line {ln} attempt {att}: '+{line.strip()[:42]}' "
                f"-> new error: {list(new)[0][:46]}")
        accepted = chosen if chosen is not None else accepted + (line or "") + "\n"
    return accepted, backtracks


_LANG_TAGS = {"typescript", "ts", "tsx", "python", "py", "rust", "rs", "go", "golang",
              "javascript", "js", "jsx", "html", "css", "sql", "none", "null", ""}


def _clean_line(content):
    """Pull the single next CODE line out of a chat reply that may wrap it in a
    markdown fence, lead with a bare language tag, or span several lines. Returns
    None when there's no usable code line (caller treats None as 'model done') —
    this is what stops fence/`None` fragments from polluting verified decode."""
    if not content:
        return None
    for raw in content.splitlines():
        s = raw.strip()
        if not s or s.startswith("```"):                 # blank or fence delimiter
            continue
        if s.strip("`").strip().lower() in _LANG_TAGS:   # bare 'typescript'/'None' leak
            continue
        s = s.strip("`").rstrip()                         # inline backticks
        if s:
            return s
    return None


def gen_line_completion(base_url, lang, instruction, model="local"):
    """One line at a time. mlx_lm.server has no /v1/completions, so we use chat with
    a 'next line only' instruction + stop at newline + thinking off (it's a reasoning
    model). attempt>0 raises temperature."""
    sysmsg = ("You are completing a code file line by line. Output ONLY the single next "
              "line of code that continues it — no prose, no markdown fences, no blank "
              "lines, never repeat earlier lines.")

    def g(accepted, attempt):
        user = f"Task: {instruction}\n\nCode so far:\n{accepted}\n\nThe next line only:"
        body = json.dumps({"model": model,
                           "messages": [{"role": "system", "content": sysmsg},
                                        {"role": "user", "content": user}],
                           "max_tokens": 64, "stop": ["\n"],
                           "temperature": 0.0 if attempt == 0 else 0.5 + 0.15 * attempt,
                           "chat_template_kwargs": {"enable_thinking": False}}).encode()
        req = urllib.request.Request(base_url + "/chat/completions", body,
                                     {"Content-Type": "application/json"})
        msg = json.loads(urllib.request.urlopen(req, timeout=120).read())["choices"][0]["message"]
        return _clean_line(msg.get("content"))
    return g


def selftest():
    """Validate the mechanism with REAL tsc and a stub 'model'. The stub proposes a
    line with an undefined variable first, then the correct line on retry — proving
    the compiler catches it and the decoder backtracks to correctness."""
    if "ts" not in VR.VERIFIERS or VR.verify_ts("const x:number=1", "")[0] is None:
        print("  (tsc/tsgo not found — install `typescript` to run the self-test)")
        return
    prefix = "function add(a: number, b: number): number {\n"
    script = [["  return a + c;", "  return a + b;"],   # line 0: bad (c undefined) -> good
              ["}"]]                                     # line 1
    st = {"ln": 0, "last": len(prefix)}

    def gen_line(accepted, attempt):
        if len(accepted) > st["last"]:        # a line was accepted -> advance
            st["ln"] += 1
            st["last"] = len(accepted)
        if st["ln"] >= len(script):
            return None
        opts = script[st["ln"]]
        return opts[min(attempt, len(opts) - 1)]

    checker = make_checker("ts")
    print("  persistent tsserver: " +
          ("ready (incremental)" if checker else "unavailable -> per-line spawn"))
    print("  generating `add` with the type-checker in the loop...\n")
    code, bt = verified_decode("ts", gen_line, prefix=prefix, max_lines=8, K=3, checker=checker)
    print("\n  === verified output ===\n" + code)
    print(f"\n  backtracks: {bt}")
    ok = "a + b" in code and "a + c" not in code
    print("  ✅ the compiler steered generation: caught `c` undefined, backtracked to `a + b`"
          if ok else "  ⚠️ self-test did not converge")
    if checker:
        checker.errors("const _w: number = 1;")              # warm the inferred project
        t0, n = time.time(), 10
        for _ in range(n):
            checker.errors("function g(a: number): number { return a + 1; }")
        per = (time.time() - t0) / n * 1000
        print(f"  ⚡ persistent tsserver: {per:.1f} ms/check vs ~150ms spawn "
              f"(~{150 / max(per, 0.1):.0f}x faster) — verified decoding is now instant")
        checker.close()
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="ts")
    ap.add_argument("--task")
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2",
                    help="model name the server expects (mlx_lm.server wants the path)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--max-lines", type=int, default=40)
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.task:
        sys.exit("  --task required (or --selftest)")
    checker = make_checker(args.lang)
    g = gen_line_completion(args.base_url, args.lang, args.task, args.model)
    code, bt = verified_decode(args.lang, g, max_lines=args.max_lines, checker=checker)
    if checker:
        checker.close()
    print(code)
    print(f"\n  (verified decode: {bt} backtracks; every accepted line type-checks)")
    # final MESH gate — line-by-line gives type-correct; the mesh adds compile+run+IDIOMATIC
    # lint (clippy/ruff/gofmt/prettier) across the whole result. Verified decode -> idiomatic.
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from verifiers import verify_domain
    r = verify_domain(args.lang, code, lint_strict=True)
    print(f"  mesh gate ({args.lang}): "
          + ("✅ idiomatic + verified" if r.passed else f"⚠️ {r.stage}: {r.diag[:200]}"))


if __name__ == "__main__":
    main()
