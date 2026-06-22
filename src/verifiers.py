"""Live-execution verifiers — the tool-fusion moat. For each language: COMPILE,
then RUN the code together with its test harness, and return the *real* runtime
result (pass/fail, which stage, the actual diagnostics, stdout). The agentic loop
(50), the multi-agent team (51), and the flywheel (52) all verify through this —
a cloud model cannot run your code in your env; we can, for free, in a loop.

  from verifiers import verify
  r = verify("python", code, harness)   # r.passed, r.stage, r.diag, r.stdout
"""
import os
import subprocess
import tempfile
from dataclasses import dataclass


@dataclass
class VResult:
    passed: bool          # compiled AND ran/tested clean (compiled, if no harness)
    stage: str            # "compile" | "run" | "ok" | "skip"
    diag: str = ""        # the real compiler/runtime diagnostics (fed to repair)
    stdout: str = ""


def _run(cmd, cwd=None, timeout=30):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except FileNotFoundError as e:                       # toolchain missing -> can't judge
        return -1, "", f"__missing__ {e}"
    except Exception as e:  # noqa: BLE001
        return 1, "", str(e)


def _result(rc, out, err, compile_stage):
    if rc == -1:
        return VResult(True, "skip", err)               # no toolchain -> neutral
    if rc != 0:
        return VResult(False, compile_stage, (err or out).strip()[:2000], out)
    return None


import sys as _sys
_PY = _sys.executable or "python3"          # bare "python" is often absent → _run rc=-1 → false PASS (the bug)


def _py(code, harness, t):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "sol.py")
        open(f, "w").write(code + "\n\n" + harness)
        rc, out, err = _run([_PY, "-m", "py_compile", f], timeout=t)
        if (r := _result(rc, out, err, "compile")):
            return r
        rc, out, err = _run([_PY, f], cwd=d, timeout=t)
        return _result(rc, out, err, "run") or VResult(True, "ok", "", out)


def _node(code, harness, t, ext):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, f"sol.{ext}")
        open(f, "w").write(code + "\n\n" + harness)
        runner = ["npx", "tsx", f] if ext == "ts" else ["node", f]
        rc, out, err = _run(runner, cwd=d, timeout=t)
        return _result(rc, out, err, "run") or VResult(True, "ok", "", out)


def _rust(code, harness, t):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "sol.rs")
        body = code + "\n\n" + harness
        if "fn main" not in body:
            body += "\nfn main(){}\n"
        open(f, "w").write(body)
        rc, out, err = _run(["rustc", "--edition", "2021", "-o",
                             os.path.join(d, "sol"), f], cwd=d, timeout=max(t, 60))
        if (r := _result(rc, out, err, "compile")):
            return r
        rc, out, err = _run([os.path.join(d, "sol")], cwd=d, timeout=t)
        return _result(rc, out, err, "run") or VResult(True, "ok", "", out)


def _go(code, harness, t):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "sol.go")
        open(f, "w").write(code + "\n\n" + harness)
        rc, out, err = _run(["go", "run", f], cwd=d, timeout=max(t, 60))
        return _result(rc, out, err, "run") or VResult(True, "ok", "", out)


def _c(code, harness, t, cpp=False):                          # #75: C / C++ via clang
    ext, cc, std = ("cpp", "clang++", "c++17") if cpp else ("c", "clang", "c11")
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, f"sol.{ext}")
        body = code + "\n\n" + harness
        if "int main" not in body:
            body += "\nint main(void){return 0;}\n"
        open(f, "w").write(body)
        rc, out, err = _run([cc, f"-std={std}", "-o", os.path.join(d, "sol"), f], cwd=d, timeout=max(t, 60))
        if (r := _result(rc, out, err, "compile")):
            return r
        rc, out, err = _run([os.path.join(d, "sol")], cwd=d, timeout=t)
        return _result(rc, out, err, "run") or VResult(True, "ok", "", out)


def _ruby(code, harness, t):                                  # #75: Ruby (syntax-check then run)
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "sol.rb")
        open(f, "w").write(code + "\n\n" + harness)
        rc, out, err = _run(["ruby", "-c", f], timeout=t)
        if (r := _result(rc, out, err, "compile")):
            return r
        rc, out, err = _run(["ruby", f], cwd=d, timeout=t)
        return _result(rc, out, err, "run") or VResult(True, "ok", "", out)


def _swift(code, harness, t):                                 # #75: Swift (compile+run)
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "sol.swift")
        open(f, "w").write(code + "\n\n" + harness)
        rc, out, err = _run(["swift", f], cwd=d, timeout=max(t, 60))
        return _result(rc, out, err, "run") or VResult(True, "ok", "", out)


_LANG = {"python": _py, "py": _py, "rust": _rust, "rs": _rust, "go": _go, "golang": _go,
         "c": _c, "cpp": lambda c, h, t: _c(c, h, t, cpp=True), "c++": lambda c, h, t: _c(c, h, t, cpp=True),
         "ruby": _ruby, "rb": _ruby, "swift": _swift}


def verify(lang, code, harness="", timeout=30):
    """COMPILE then RUN code+harness. Returns VResult. Unknown lang -> skip (neutral)."""
    lang = (lang or "").lower()
    if lang in _LANG:
        return _LANG[lang](code, harness, timeout)
    if lang in ("ts", "typescript", "tsx"):
        return _node(code, harness, timeout, "ts")
    if lang in ("js", "javascript", "jsx", "node"):
        return _node(code, harness, timeout, "js")
    return VResult(True, "skip", f"no verifier for {lang!r}")


# ---- the verifier MESH: linters (idiomatic) + SQL + a unified per-domain entry -------

def _clippy(code, timeout):
    with tempfile.TemporaryDirectory() as d:
        proj = os.path.join(d, "p")
        if _run(["cargo", "new", "--lib", "--quiet", proj], timeout=40)[0] != 0:
            return True, "clippy unavailable"
        open(os.path.join(proj, "src", "lib.rs"), "w").write(code)
        rc, out, err = _run(["cargo", "clippy", "--quiet", "--message-format", "short"],
                            cwd=proj, timeout=max(timeout, 120))
        warns = "\n".join(l for l in (out + err).splitlines() if "warning:" in l)
        return (rc == 0 and "warning:" not in (out + err)), warns[:1500]


def lint(lang, code, timeout=40):
    """Idiomatic linter -> (clean, warnings). Best-effort; (True,'') if the tool is absent
    so it never blocks. clippy/ruff/gofmt/prettier upgrade 'compiles' -> 'idiomatic'."""
    lang = (lang or "").lower()
    with tempfile.TemporaryDirectory() as d:
        if lang in ("python", "py"):
            f = os.path.join(d, "s.py"); open(f, "w").write(code)
            rc, out, err = _run(["ruff", "check", "--quiet", f], timeout=timeout)
            return (rc != 0) is False if rc != -1 else True, (out or err)[:1200] if rc > 0 else ""
        if lang in ("go", "golang"):
            f = os.path.join(d, "s.go"); open(f, "w").write(code)
            rc, out, _ = _run(["gofmt", "-l", f], timeout=timeout)
            return (not out.strip()) if rc != -1 else True, ("not gofmt-clean" if out.strip() else "")
        if lang in ("rust", "rs"):
            return _clippy(code, timeout)
        if lang in ("js", "javascript", "ts", "typescript", "tsx", "jsx"):
            ext = "ts" if "ts" in lang else "js"
            f = os.path.join(d, f"s.{ext}"); open(f, "w").write(code)
            rc, out, err = _run(["npx", "--no-install", "prettier", "--check", f], timeout=timeout)
            return (rc == 0) if rc != -1 else True, ("not prettier-formatted" if rc > 0 else "")
    return True, ""


def verify_sql(sql, setup="", timeout=20):
    """Run SQL against Postgres if DATABASE_URL is set (niche upgrade), otherwise fall back
    to SQLite (in-memory). Catches dialect syntax + runtime errors for queries and migrations.
    Uses rollback to keep the execution side-effect free."""
    dsn = os.environ.get("DATABASE_URL")
    if dsn:
        try:
            import psycopg
            # Postgres verification
            with psycopg.connect(dsn, autocommit=False, timeout=timeout) as con:
                with con.cursor() as cur:
                    if setup:
                        cur.execute(setup)
                    cur.execute(sql)
                # Rollback changes to keep the database clean
                con.rollback()
            return VResult(True, "ok", "")
        except ImportError:
            pass                                          # psycopg not installed → SQLite fallback
        except psycopg.OperationalError:
            pass                                          # can't REACH Postgres (DB down / bad DSN) → fall back to SQLite, NOT a false-FAIL of valid SQL
        except Exception as e:  # noqa: BLE001
            return VResult(False, "run", f"PostgreSQL error: {str(e)[:300]}")

    # SQLite fallback
    import sqlite3 as s3
    try:
        con = s3.connect(":memory:")
        if setup:
            con.executescript(setup)
        (con.executescript if sql.count(";") > 1 else con.execute)(sql)
        con.commit(); con.close()
        return VResult(True, "ok", "")
    except Exception as e:  # noqa: BLE001
        return VResult(False, "run", f"SQL error: {str(e)[:300]}")


def verify_lean(proof, timeout=120):
    """Correct-by-construction MATH — run Lean 4 on the proof; pass iff Lean accepts it
    (no `sorry`, no errors). Best-effort: 'skip' if lean isn't installed (elan to activate)."""
    import shutil
    lean = shutil.which("lean") or os.path.expanduser("~/.elan/bin/lean")
    lake = shutil.which("lake") or os.path.expanduser("~/.elan/bin/lake")
    # Use the lean-verify mathlib project when present → positivity/nlinarith/ring/field_simp/... available.
    # Without this, mathlib proofs FAIL verification (the cap that understated miniF2F). Falls back to standalone.
    proj = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lean-verify"))
    use_mathlib = os.path.isdir(os.path.join(proj, ".lake", "packages", "mathlib"))
    if use_mathlib and "import Mathlib" not in proof:
        proof = "import Mathlib.Tactic\n" + proof
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "Proof.lean")
        open(f, "w").write(proof)
        cmd = [lake, "env", lean, f] if use_mathlib else [lean, f]
        rc, out, err = _run(cmd, cwd=proj if use_mathlib else d, timeout=timeout)
        if rc == -1:
            return VResult(True, "skip", "lean not installed (run: curl elan-init | sh)")
        blob = out + err
        if re.search(r"\bsorry\b", proof) and "warning" in blob.lower():   # unfinished proof (word-bound: not 'not_sorry')
            return VResult(False, "lean", "proof contains `sorry` (incomplete)")
        return _result(rc, out, err, "lean") or VResult(True, "ok", "Lean: proof accepted ✓")


def _verify_design(html):
    """Render the HTML (Playwright) + measure it (WCAG/type-scale/OKLCH/framework-tells)
    via scripts/25_design_critique — the DESIGN half of the niche, in the mesh."""
    import importlib.util
    p = os.path.join(os.path.dirname(__file__), "..", "scripts", "25_design_critique.py")
    if not os.path.exists(p):
        return VResult(True, "skip", "design critic (25) not found")
    spec = importlib.util.spec_from_file_location("dc", p)
    dc = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(dc)
        page = dc.extract_html(html) if hasattr(dc, "extract_html") else html
        findings = dc.critique(page, dc.measure(page, "/tmp/_verify_design.png"))
        return VResult(len(findings) == 0, "design", "; ".join(map(str, findings[:6])))
    except Exception as e:  # noqa: BLE001
        return VResult(False, "design", f"render/critique error: {str(e)[:200]}")


def verify_domain(domain, output, *, harness="", lint_strict=False, setup="", **_):
    """ONE call the agent + verified-decoding use for EVERY domain — the verifier mesh.
    Routes to the right real tool and returns a uniform VResult. Covers the FULL niche:
    code (compile+run+lint), SQL, math, and DESIGN (render+measure)."""
    d = (domain or "").lower()
    if d in ("design", "html", "css"):
        return _verify_design(output)
    if d in ("lean", "proof"):
        return verify_lean(output)
    if d in ("sql", "postgres", "psql"):
        return verify_sql(output, setup)
    if d == "math":
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        from sci_tools import sympy_eval
        r = sympy_eval(output)
        return VResult("FALSE" not in r and "error" not in r.lower(), "math", r)
    import concurrent.futures as _cf              # compile+run AND lint CONCURRENTLY (independent -> two cores)
    with _cf.ThreadPoolExecutor(max_workers=2) as _ex:
        _fv, _fl = _ex.submit(verify, d, output, harness), _ex.submit(lint, d, output)
        res = _fv.result()
        if not res.passed:
            return res                            # lint ran in parallel; discard it — no extra wall-time
        clean, warns = _fl.result()
    if not clean and lint_strict:
        return VResult(False, "lint", f"not idiomatic: {warns}", res.stdout)
    if not clean:
        res.diag = f"(lint: {warns[:300]})"
    return res


def verify_many(items, *, workers=None, fn=verify_domain):
    """Verify MANY candidates in PARALLEL across all cores — the Super-Core fan-out.

    Each verifier is a subprocess (compile / run / Lean / SQL) that releases the GIL
    on its I/O, so a thread pool spreads them across the 6 Super + 12 Performance
    cores (macOS schedules the compute-heavy children on the fast cores). Turns a
    serial best-of-N verify (N x ~one verifier) into ~one verifier wall-clock.

      results = verify_many([{"domain":"python","output":c,"harness":h} for c in cands])
      results = verify_many([("lean", p) for p in proofs])   # positional also ok

    `items`: list of dicts (passed as kwargs to `fn`) or tuples (positional).
    Returns VResults in INPUT ORDER. `fn` defaults to the full verifier mesh.
    """
    import concurrent.futures as _cf

    items = list(items)
    if not items:
        return []
    if workers is None:
        workers = min(len(items), (os.cpu_count() or 8))

    def _one(it):
        return fn(**it) if isinstance(it, dict) else fn(*it)

    with _cf.ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, items))   # ex.map preserves input order
