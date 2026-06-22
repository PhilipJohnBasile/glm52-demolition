"""#4 Multi-language flywheel — RUST lane (mirrors recover_datagen_diverse.py for Rust).

Our stack is Rust-heavy (callsieve), so the recovery corpus shouldn't be Python-only. Same recipe:
take a correct Rust fn+test, inject a test-breaking mutation, best-of-N a fix, keep only cargo-verified.

The mutate->verify core is SERVE-FREE (cargo only) and is tested below without the model. Generation
(best-of-N) uses the serve at :8080 — run this ONLY when the Python flywheel is paused (one big model,
never concurrent: concurrent generation OOM-killed the serve twice).

  python scripts/recover_datagen_rust.py --selftest      # mutate->verify core, NO model (safe anytime)
  python scripts/recover_datagen_rust.py 300             # full run — ONLY when serve is free
"""
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

BASE = "http://localhost:8080/v1/chat/completions"

# verifiers.py's rust path is clippy (compile-only) — it can't catch a test-breaking bug that still
# compiles (== -> != compiles fine). The flywheel needs REAL test execution, so we run `cargo test`
# against a single reused project (first compile ~10s, then incremental — fast enough for many checks).
_PROJ = None


def _proj():
    global _PROJ
    if _PROJ is None:
        d = tempfile.mkdtemp()
        subprocess.run(["cargo", "new", "--lib", "--quiet", os.path.join(d, "p")], check=True,
                       capture_output=True)
        _PROJ = os.path.join(d, "p")
    return _PROJ


def cargo_test(code, test):
    """True iff `code`+`test` compiles AND the tests pass (real execution, not just clippy)."""
    p = _proj()
    open(os.path.join(p, "src", "lib.rs"), "w").write(code + "\n" + test + "\n")
    try:
        r = subprocess.run(["cargo", "test", "--quiet"], cwd=p, capture_output=True, text=True, timeout=120)
        return r.returncode == 0
    except Exception:
        return False

# Rust bug families (operator-flips + boundary + boolean + return-literal), mirroring the Python set.
RUST_MUTS = [(" + 1", " - 1"), (" - 1", " + 1"), (" < ", " <= "), (" <= ", " < "), (" > ", " >= "),
             (" == ", " != "), (" != ", " == "), (" && ", " || "), (" || ", " && "),
             (".min(", ".max("), (".max(", ".min("), ("return true", "return false"),
             ("return false", "return true"), (" * ", " + "), ("[0]", "[1]"), (".iter()", ".iter().rev()")]

# Self-contained Rust fn + test pairs (the seed corpus; extend by mining callsieve's pure fns).
SAMPLES = [
    ("pub fn add(a: i32, b: i32) -> i32 { a + b }",
     "#[cfg(test)] mod tests { use super::*; #[test] fn t() { assert_eq!(add(2,3),5); assert_eq!(add(10,5),15); } }"),
    ("pub fn max_of(v: &[i32]) -> i32 { let mut m = v[0]; for &x in v { if x > m { m = x; } } m }",
     "#[cfg(test)] mod tests { use super::*; #[test] fn t() { assert_eq!(max_of(&[1,9,3]),9); assert_eq!(max_of(&[5,2]),5); } }"),
    ("pub fn is_even(n: i32) -> bool { n % 2 == 0 }",
     "#[cfg(test)] mod tests { use super::*; #[test] fn t() { assert!(is_even(4)); assert!(!is_even(3)); } }"),
    ("pub fn count_pos(v: &[i32]) -> usize { v.iter().filter(|&&x| x > 0).count() }",
     "#[cfg(test)] mod tests { use super::*; #[test] fn t() { assert_eq!(count_pos(&[-1,2,3,-4]),2); } }"),
]


def gen(prompt, temp=0.4, max_tokens=400):
    body = json.dumps({"messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens,
                       "temperature": temp, "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(BASE, body, {"content-type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())["choices"][0]["message"]["content"]


def extract(text):
    import re
    m = re.search(r"```(?:rust|rs)?\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


def main():
    selftest = "--selftest" in sys.argv
    N = 5
    target = int(next((a for a in sys.argv[1:] if a.isdigit()), 300))
    out = open("recover_data_rust.jsonl", "a") if not selftest else None
    kept = 0
    for code, tests in SAMPLES:
        if not cargo_test(code, tests):   # canonical must pass
            print(f"  skip (canonical fails): {code[:40]}", flush=True)
            continue
        bugs = []
        for find, repl in RUST_MUTS:
            if find in code and len(bugs) < 3:
                cand = code.replace(find, repl, 1)
                if not cargo_test(cand, tests):
                    bugs.append((find, repl, cand))
        if selftest:
            print(f"  ✓ {code[:34]!r}: {len(bugs)} real bugs (mutate->cargo-verify works)", flush=True)
            kept += len(bugs)
            continue
        for find, repl, buggy in bugs:
            prompt = (f"This Rust code has a bug; the test fails:\n```rust\n{buggy}\n{tests}\n```\n"
                      f"Output ONLY the corrected function (valid Rust).")
            with cf.ThreadPoolExecutor(max_workers=N) as ex:
                cands = list(ex.map(lambda i: extract(gen(prompt, 0.4 + 0.12 * i)), range(N)))
            for c in cands:
                if c and c.strip() != buggy.strip() and cargo_test(c, tests):
                    out.write(json.dumps({"messages": [{"role": "user", "content": prompt},
                                                        {"role": "assistant", "content": c}]}) + "\n")
                    out.flush()
                    kept += 1
                    print(f"  ✓ kept rust {find!r}->{repl!r} (total {kept})", flush=True)
                    break
            if kept >= target:
                break
        if kept >= target:
            break
    print(f"  RUST {'SELFTEST' if selftest else 'corpus'}: {kept} {'bugs found' if selftest else 'verified fixes'}")
    if selftest and kept:
        print("  SELFTEST OK — Rust mutate->verify pipeline works (gen deferred until serve free)")


if __name__ == "__main__":
    main()
