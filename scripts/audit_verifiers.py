"""Verifier-mesh audit (#26, the standing rule: always audit verifiers with good+bad). Run a GOOD (correct)
and a BAD (compiles-but-WRONG -> fails its own test) snippet through every language verifier and confirm it
DISCRIMINATES. The known risk (verifiers.py:38): a missing toolchain returns passed=True ("skip") -> every
snippet in that language silently false-passes -> its heal gold was never actually verified. This finds which
languages are solid vs silently-skipped vs buggy.

  python scripts/audit_verifiers.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from verifiers import verify

# (lang, GOOD = correct & compiles & passes, BAD = compiles but WRONG answer -> must FAIL at run)
CASES = [
    ("python", "def f(x): return x*2\nassert f(3)==6", "def f(x): return x*3\nassert f(3)==6"),
    ("js", "function f(x){return x*2}\nif(f(3)!==6)process.exit(1)", "function f(x){return x*3}\nif(f(3)!==6)process.exit(1)"),
    ("ts", "function f(x:number){return x*2}\nif(f(3)!==6)process.exit(1)", "function f(x:number){return x*3}\nif(f(3)!==6)process.exit(1)"),
    ("rust", "fn f(x:i32)->i32{x*2}\nfn main(){assert_eq!(f(3),6);}", "fn f(x:i32)->i32{x*3}\nfn main(){assert_eq!(f(3),6);}"),
    ("go", 'package main\nimport "os"\nfunc f(x int)int{return x*2}\nfunc main(){if f(3)!=6{os.Exit(1)}}',
     'package main\nimport "os"\nfunc f(x int)int{return x*3}\nfunc main(){if f(3)!=6{os.Exit(1)}}'),
    ("c", "int f(int x){return x*2;}\nint main(){return f(3)==6?0:1;}", "int f(int x){return x*3;}\nint main(){return f(3)==6?0:1;}"),
    ("cpp", "int f(int x){return x*2;}\nint main(){return f(3)==6?0:1;}", "int f(int x){return x*3;}\nint main(){return f(3)==6?0:1;}"),
    ("ruby", "def f(x); x*2; end\nraise unless f(3)==6", "def f(x); x*3; end\nraise unless f(3)==6"),
    ("swift", "func f(_ x:Int)->Int{return x*2}\nassert(f(3)==6)", "func f(_ x:Int)->Int{return x*3}\nassert(f(3)==6)"),
]


def main():
    rows, skips, bugs = [], [], []
    for lang, good, bad in CASES:
        g, b = verify(lang, good), verify(lang, bad)
        if g.stage == "skip" or b.stage == "skip":
            verdict, _ = "⚠️  SKIP — toolchain missing → UNVERIFIED (silent false-pass)", skips.append(lang)
        elif not g.passed:
            verdict, _ = f"❌ FALSE-FAIL — good rejected @ {g.stage}: {g.diag[:40]}", bugs.append(lang)
        elif b.passed:
            verdict, _ = "❌ FALSE-PASS — wrong code ACCEPTED", bugs.append(lang)
        else:
            verdict = f"✅ OK — good={g.stage}, bad caught @ {b.stage}"
        rows.append((lang, verdict))
    print("  VERIFIER-MESH AUDIT — good vs compiles-but-WRONG:")
    for lang, v in rows:
        print(f"    {lang:7} {v}")
    solid = len(CASES) - len(skips) - len(bugs)
    print(f"  --- {solid}/{len(CASES)} solid · {len(skips)} skipped [{','.join(skips) or '-'}] · {len(bugs)} buggy [{','.join(bugs) or '-'}]")
    if skips:
        print("  ⚠️  skipped langs silently pass their gold — install the toolchain OR drop that gold from the heal.")
    if bugs:
        print("  ❌ real bug(s) — fix before the next heal.")


if __name__ == "__main__":
    main()
