"""Integrity layer — stops the agent LYING about what it did (the worst 2026 failures: fabricated
reports, tampered tests, scope creep, slopsquatted deps). Our thesis crystallized: the VERIFIER is
the incorruptible source of truth; the agent's word is never trusted.
 1. guard_test_edit — block/flag weakening or deleting a test to fake a pass.
 2. done_has_proof  — 'done' requires REAL verifier evidence, not a claim.
 3. scope_check     — flag edits to sensitive / out-of-scope files.
 4. check_install   — verify packages exist on the real registry before install (anti-slopsquat).
"""
import re
import urllib.request

# ---- 1. test-tamper guard --------------------------------------------------------------
_TESTFILE = re.compile(r"(^|/)(tests?/|test_|.*[._]test\.|.*\.spec\.|conftest\.)", re.I)
_ASSERT = re.compile(r"(assert|expect|should|assert_eq!|assert!|XCTAssert|t\.(Error|Fatal)|require\.|chai)", re.I)
_SKIP = re.compile(r"@(?:pytest\.mark\.)?(?:skip|xfail)|\.skip\(|it\.skip|describe\.skip|t\.Skip|#\[ignore\]", re.I)


def is_test_file(path):
    return bool(_TESTFILE.search(path or ""))


def guard_test_edit(path, old, new, task=""):
    """Flag test-tampering: WEAKENING a test (fewer asserts, added skips, big deletions). When the
    task is 'make the tests pass', that's reward-hacking -> BLOCK. Otherwise -> warn."""
    if not is_test_file(path):
        return ""
    w = []
    if len(_ASSERT.findall(new or "")) < len(_ASSERT.findall(old or "")):
        w.append("removed assertions")
    if _SKIP.search(new or "") and not _SKIP.search(old or ""):
        w.append("added skip/xfail")
    if old and len(new or "") < len(old) * 0.6:
        w.append("deleted >40% of the test")
    if not w:
        return ""
    if re.search(r"(make|get|fix).{0,25}(test|spec).{0,12}(pass|green)|fix.{0,15}\btest", task or "", re.I):
        return (f"🚫 BLOCKED (test-tamper): {w} on a TEST file while the task is to make tests pass — "
                "that's reward-hacking. Fix the CODE, not the test.")
    return f"⚠️ test-integrity: {w} — confirm you mean to change the test, not weaken it."


# ---- 2. fabrication-proof 'done' -------------------------------------------------------
_PASS = re.compile(r"exit=0|all tests pass|passed=True|tests? passed|0 failed|build succeeded|\bok\b", re.I)
_FAIL = re.compile(r"exit=[1-9]|test result:\s*failed|[1-9]\d*\s*(?:failed|failures|errors?)|"
                   r"\bpanic|traceback|\bexception\b|error\[E\d", re.I)  # \bpanic catches panicked;
# error\[E\d catches rustc codes. NOT bare 'fail'/'error' — cargo's pass line says "0 failed", which a
# naive \bfail tripped → a PASSING agent's `done` got rejected (exit=[1-9] is the main catch anyway).


def done_has_proof(recent_obs):
    """A 'done' must be backed by a REAL verifier pass in recent observations (no fabrication)."""
    for o in list(recent_obs)[-6:][::-1]:
        s = str(o)
        if _PASS.search(s) and not _FAIL.search(s):
            return True
    return False


# ---- 3. scope enforcement --------------------------------------------------------------
_SENSITIVE = re.compile(r"(^|/)(\.env|\.git/|.*\.lock$|package-lock|.*\.ya?ml$|Dockerfile|\.github/|"
                        r"secrets?|credentials|id_rsa|prod)", re.I)


def scope_check(path, touched, limit=12):
    w = []
    if _SENSITIVE.search(path or ""):
        w.append(f"sensitive file '{path}'")
    if len(touched) >= limit:
        w.append(f"{len(touched)} files touched (scope creep?)")
    return ("⚠️ scope: " + "; ".join(w) + " — confirm this is in-scope.") if w else ""


# ---- 4. slopsquat / dep-existence guard ------------------------------------------------
_REG = {"py": "https://pypi.org/pypi/{}/json", "js": "https://registry.npmjs.org/{}",
        "rs": "https://crates.io/api/v1/crates/{}"}
_ECO = {"pip": "py", "pip3": "py", "uv": "py", "npm": "js", "pnpm": "js", "yarn": "js", "cargo": "rs"}


def _exists(pkg, eco):
    try:
        req = urllib.request.Request(_REG[eco].format(pkg), headers={"User-Agent": "dep-check"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return 200 <= r.status < 300
    except Exception:  # noqa: BLE001
        return False


def check_install(cmd):
    """Anti-slopsquat: before an install command runs, verify the packages exist on the real
    registry (hallucinated/typo'd names are the supply-chain vector). Empty string = OK."""
    m = re.search(r"\b(uv pip|pip3?|npm|pnpm|yarn|cargo)\s+(?:install|add)\s+(.+)", cmd or "")
    if not m:
        return ""
    eco = _ECO.get(m.group(1).split()[0])
    if not eco:
        return ""
    names = [p.split("==")[0].split("@")[0].split("~")[0].strip()
             for p in m.group(2).split() if not p.startswith("-")]
    missing = [p for p in names if p and not _exists(p, eco)]
    return (f"🚫 BLOCKED (slopsquat): {missing} NOT on the {eco} registry — hallucinated or typo'd. "
            "Verify the exact package name before installing." if missing else "")


def selftest():
    tamper = "BLOCKED" in guard_test_edit("tests/test_x.py", "def test_a():\n assert f()==1\n",
                                           "def test_a():\n pass\n", "make the tests pass")
    proof = done_has_proof(["exit=0\nall tests passed"]) and not done_has_proof(["exit=1 FAILED"])
    scope = "sensitive" in scope_check(".env", [])
    ok = tamper and proof and scope
    print(f"  integrity selftest: test-tamper={tamper} done-proof={proof} scope={scope}  "
          f"{'PASS ✅' if ok else 'FAIL'} (slopsquat needs network)")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
