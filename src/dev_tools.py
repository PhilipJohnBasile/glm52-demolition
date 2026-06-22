"""Senior-engineer dev tools for the agent — the worth-it gaps after a cost/benefit dive:
- git  : status/diff/log/branch/commit + open a PR (gh). The agent SHIPS changes, not just edits.
- profile : cProfile a Python snippet -> hot paths (performance, not just correctness).
- pg   : run SQL against a REAL Postgres (DATABASE_URL via psycopg), sqlite fallback.
- code_intel : LSP semantic nav (definition/references/hover via pyright/rust-analyzer),
               with a grep fallback so it always returns something useful.
Wired into the tool-agent (scripts/57).
"""
import json
import os
import subprocess


def _sh(cmd, cwd=None, timeout=90):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


# ---- git + PR --------------------------------------------------------------------------
def git(action, repo=".", **kw):
    a = (action or "").lower()
    if a == "status":
        return _sh(["git", "status", "--short", "--branch"], repo)[1] or "(clean)"
    if a == "diff":
        return _sh(["git", "diff"] + (["--staged"] if kw.get("staged") else []), repo)[1][:3000] or "(no diff)"
    if a == "log":
        return _sh(["git", "log", "--oneline", "-15"], repo)[1]
    if a == "branch":
        return _sh(["git", "checkout", "-b", kw["name"]], repo)[1] or f"switched to new branch {kw['name']}"
    if a == "commit":
        _sh(["git", "add", "-A"], repo)
        return _sh(["git", "commit", "-m", kw.get("message", "agent commit")], repo)[1]
    if a == "pr":                                          # open a reviewable PR via gh
        return _sh(["gh", "pr", "create", "--title", kw.get("title", "agent change"),
                    "--body", kw.get("body", "Automated change; tests green.")], repo)[1]
    return f"unknown git action {action!r} (status/diff/log/branch/commit/pr)"


# ---- profiler --------------------------------------------------------------------------
def profile(code, timeout=30):
    """cProfile a Python snippet -> the top cumulative-time functions (hot paths)."""
    import sys                                            # used below (sys.executable) — was a NameError crash
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "p.py")
        open(f, "w").write(code)
        rc, out = _sh([sys.executable, "-m", "cProfile", "-s", "cumtime", f], d, timeout)
        if rc != 0:
            return f"profile error:\n{out[-800:]}"
        lines = [l for l in out.splitlines() if l.strip()]
        head = lines[:14]                                  # header + top hot functions
        return "hot paths (cumulative time):\n" + "\n".join(head)


# ---- real Postgres (or sqlite fallback) ------------------------------------------------
def pg(sql, dsn=None, setup=""):
    dsn = dsn or os.environ.get("DATABASE_URL")
    if dsn:
        try:
            import psycopg
            with psycopg.connect(dsn, autocommit=True) as c, c.cursor() as cur:
                if setup:
                    cur.execute(setup)
                cur.execute(sql)
                rows = cur.fetchall() if cur.description else []
                return f"postgres ok ({len(rows)} rows): {rows[:10]}"
        except Exception as e:  # noqa: BLE001
            return f"postgres error: {str(e)[:300]}"
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from verifiers import verify_sql                       # sqlite fallback (no DATABASE_URL)
    r = verify_sql(sql, setup)
    return f"(no DATABASE_URL — sqlite fallback) {'ok' if r.passed else r.diag}"


# ---- LSP code-intelligence (semantic nav) ----------------------------------------------
os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + os.path.expanduser("~/go/bin")  # gopls installs here, not on default PATH
_SERVERS = {                                                  # the model's target langs; a missing server skips gracefully (which() check in _lsp)
    ".py": ["pyright-langserver", "--stdio"], ".rs": ["rust-analyzer"], ".go": ["gopls"],
    ".ts": ["typescript-language-server", "--stdio"], ".tsx": ["typescript-language-server", "--stdio"],
    ".js": ["typescript-language-server", "--stdio"], ".jsx": ["typescript-language-server", "--stdio"],
    ".c": ["clangd"], ".cpp": ["clangd"], ".cc": ["clangd"], ".h": ["clangd"], ".hpp": ["clangd"],
}


def _lsp(repo, rel, line, col, method, timeout=25):
    ext = os.path.splitext(rel)[1]
    cmd = _SERVERS.get(ext)
    if not cmd or not __import__("shutil").which(cmd[0]):
        return None
    import time
    proc = subprocess.Popen(cmd, cwd=repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL)

    def send(o):
        b = json.dumps(o).encode()
        proc.stdin.write(b"Content-Length: %d\r\n\r\n%s" % (len(b), b)); proc.stdin.flush()

    def recv():
        n = 0
        while True:
            ln = proc.stdout.readline()
            if ln in (b"\r\n", b"\n", b""):
                break
            if ln.lower().startswith(b"content-length"):
                n = int(ln.split(b":")[1])
        return json.loads(proc.stdout.read(n)) if n else {}

    root = "file://" + os.path.realpath(repo)
    uri = "file://" + os.path.realpath(os.path.join(repo, rel))
    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"processId": os.getpid(), "rootUri": root, "capabilities": {}}})
        t0 = time.time()
        while recv().get("id") != 1 and time.time() - t0 < timeout:
            pass
        send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
        send({"jsonrpc": "2.0", "method": "textDocument/didOpen", "params": {"textDocument": {
            "uri": uri, "languageId": ext[1:], "version": 1, "text": open(os.path.join(repo, rel)).read()}}})
        time.sleep(2.0 if ext == ".rs" else 0.4)           # let the server index
        send({"jsonrpc": "2.0", "id": 2, "method": method,
              "params": {"textDocument": {"uri": uri}, "position": {"line": line, "character": col}}})
        t0 = time.time()
        while time.time() - t0 < timeout:
            m = recv()
            if m.get("id") == 2:
                return m.get("result")
    except Exception:  # noqa: BLE001
        return None
    finally:
        proc.terminate()
    return None


def code_intel(action, repo, file, line=0, col=0, symbol=""):
    """definition | references | hover via LSP; grep fallback (text-based) if LSP unavailable."""
    method = {"definition": "textDocument/definition", "references": "textDocument/references",
              "hover": "textDocument/hover"}.get(action, "textDocument/definition")
    res = _lsp(repo, file, int(line), int(col), method)
    if res:
        return f"LSP {action}: {json.dumps(res)[:1200]}"
    # fallback: grep the symbol (definitions: def/fn/class/struct; references: all hits)
    sym = symbol or "?"
    if action == "definition":
        p = subprocess.run(["grep", "-rnE", rf"(def|fn|class|struct|impl|type) +{sym}", "."],
                           cwd=repo, capture_output=True, text=True)
        return f"(grep def {sym}) " + (p.stdout[:1200] or "not found")
    p = subprocess.run(["grep", "-rn", sym, "."], cwd=repo, capture_output=True, text=True)
    return f"(grep refs {sym}) " + (p.stdout[:1500] or "not found")


# ---- structured edit (apply_patch) -----------------------------------------------------
def apply_patch(repo, file, old, new):
    """Reliable structured edit: replace `old` with `new` (must match EXACTLY and UNIQUELY)
    instead of rewriting the whole file — what frontier agents use for big files."""
    repo_real = os.path.realpath(repo)
    p = os.path.realpath(os.path.join(repo, file))
    if p != repo_real and not p.startswith(repo_real + os.sep):     # trailing sep: block sibling-prefix escape (myrepo-evil)
        return "path escapes repo"
    if not os.path.exists(p):
        return "no such file"
    s = open(p).read()
    c = s.count(old)
    if c != 1:
        # lenient fallback: small/quantized models pad `old`/`new` with imperfect surrounding
        # context (a guessed comment line). If the LAST non-blank line of `old` is unique, edit
        # just that line — the real change lands without needing perfect context reproduction.
        ol = [l for l in old.splitlines() if l.strip()]
        nl = [l for l in new.splitlines() if l.strip()]
        # The model usually changes ONE line but pads `old` with mis-guessed context. Find the single
        # changed line (in old, not new) + its replacement (in new, not old) and edit JUST it —
        # position-independent (the LAST line is often `}`, not unique). Aider's lesson: be
        # whitespace-flexible (quantized models mis-indent constantly).
        chg_o = [l for l in ol if l not in nl]
        chg_n = [l for l in nl if l not in ol]
        if len(chg_o) == 1 and len(chg_n) == 1:
            if s.count(chg_o[0]) == 1:                                  # exact, unique
                open(p, "w").write(s.replace(chg_o[0], chg_n[0], 1))
                return f"patched {file} (changed-line)"
            flines = s.split("\n")                                      # whitespace-flexible, unique
            hits = [i for i, l in enumerate(flines) if l.strip() == chg_o[0].strip()]
            if len(hits) == 1:
                indent = flines[hits[0]][:len(flines[hits[0]]) - len(flines[hits[0]].lstrip())]
                flines[hits[0]] = indent + chg_n[0].strip()
                open(p, "w").write("\n".join(flines))
                return f"patched {file} (changed-line, ws-flex)"
        if ol and nl and s.count(ol[-1]) == 1:                         # original last-line fallback
            open(p, "w").write(s.replace(ol[-1], nl[-1], 1))
            return f"patched {file} (1 hunk, line-match fallback)"
        # self-correcting: show the ACTUAL code near the target so the model stops re-emitting a
        # doomed `old` (small models pad it with a hallucinated comment that doesn't match the file).
        anchor = ol[-1].strip() if ol else ""
        hint = ""
        if anchor:
            lines = s.splitlines()
            locs = [i for i, ln in enumerate(lines) if anchor in ln]
            if locs:
                i = locs[0]
                hint = "\n  actual code there (copy it VERBATIM as `old`):\n" + "\n".join(
                    lines[max(0, i - 2):i + 3])
        return (f"old text matches {c}× — it does not match the file. Use the EXACT current text "
                f"as `old`.{hint}")
    open(p, "w").write(s.replace(old, new))
    return f"patched {file} (1 hunk)"


# ---- GitHub connector (gh api) ---------------------------------------------------------
def github(action, repo=".", **kw):
    a = (action or "").lower()
    if a == "issues":
        return _sh(["gh", "issue", "list", "--limit", "20"], repo)[1] or "(no issues)"
    if a == "issue":
        return _sh(["gh", "issue", "view", str(kw.get("number", ""))], repo)[1]
    if a == "prs":
        return _sh(["gh", "pr", "list", "--limit", "20"], repo)[1] or "(no PRs)"
    if a == "api":
        return _sh(["gh", "api", kw.get("path", "user")], repo)[1][:2000]
    return f"unknown github action {action!r} (issues/issue/prs/api)"


# ---- documents (PDF / docx) ------------------------------------------------------------
def read_doc(path):
    e = os.path.splitext(path)[1].lower()
    try:
        if e == ".pdf":
            import pypdf
            return "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(path).pages)[:6000]
        if e == ".docx":
            import docx
            return "\n".join(p.text for p in docx.Document(path).paragraphs)[:6000]
        return open(path).read()[:6000]
    except Exception as e2:  # noqa: BLE001
        return f"read_doc error: {str(e2)[:150]}"


# ---- desktop computer-use (pyautogui) --------------------------------------------------
def desktop(action, **kw):
    """Full-desktop control (beyond the browser). Needs macOS Accessibility permission to act."""
    try:
        import pyautogui
    except Exception as e:  # noqa: BLE001
        return f"pyautogui unavailable: {str(e)[:80]}"
    a = (action or "").lower()
    try:
        if a == "screenshot":
            path = kw.get("path", "/tmp/desktop.png"); pyautogui.screenshot(path); return path
        if a == "click":
            pyautogui.click(int(kw["x"]), int(kw["y"])); return f"clicked {kw['x']},{kw['y']}"
        if a == "type":
            pyautogui.typewrite(kw.get("text", ""), interval=0.01); return "typed"
        if a == "key":
            pyautogui.press(kw["key"]); return f"pressed {kw['key']}"
        return f"unknown desktop action {action!r} (screenshot/click/type/key)"
    except Exception as e:  # noqa: BLE001
        return f"desktop error (grant Accessibility in System Settings?): {str(e)[:120]}"


# ---- generic MCP connector client ------------------------------------------------------
def mcp_call(server, tool, args=None, config=".mcp.json"):
    """Call a tool on a configured MCP server — the connector mechanism (GitHub/Slack/Notion/
    Postgres/… via .mcp.json). Minimal stdio JSON-RPC client; best-effort."""
    if not os.path.exists(config):
        return f"no {config} (configure MCP servers there)"
    cfg = json.load(open(config)).get("mcpServers", {}).get(server)
    if not cfg:
        return f"server {server!r} not in {config}"
    proc = subprocess.Popen([cfg["command"]] + cfg.get("args", []), stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            env={**os.environ, **cfg.get("env", {})}, text=True)
    try:
        for msg in ('{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":'
                    '"2024-11-05","capabilities":{},"clientInfo":{"name":"agent","version":"1"}}}',
                    '{"jsonrpc":"2.0","method":"notifications/initialized"}',
                    json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                "params": {"name": tool, "arguments": args or {}}})):
            proc.stdin.write(msg + "\n"); proc.stdin.flush()
        for _ in range(8):
            line = proc.stdout.readline()
            if line and '"id":2' in line:
                return json.dumps(json.loads(line).get("result", {}))[:2000]
        return "(no result)"
    except Exception as e:  # noqa: BLE001
        return f"mcp error: {str(e)[:150]}"
    finally:
        proc.terminate()


def selftest():
    import tempfile
    repo = tempfile.mkdtemp()
    _sh(["git", "init", "-q"], repo)
    open(os.path.join(repo, "a.py"), "w").write("def add(a, b):\n    return a + b\n")
    ok_git = "a.py" in git("status", repo)
    ok_prof = "cumulative" in profile("sum(range(100000))")
    ok_pg = "ok" in pg("SELECT 1").lower()
    ok_ci = "add" in code_intel("definition", repo, "a.py", symbol="add")
    print(f"  dev_tools selftest: git={ok_git} profile={ok_prof} pg(sqlite)={ok_pg} "
          f"code_intel={ok_ci}  {'PASS ✅' if all([ok_git, ok_prof, ok_pg, ok_ci]) else 'FAIL'}")
    return all([ok_git, ok_prof, ok_pg, ok_ci])


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
