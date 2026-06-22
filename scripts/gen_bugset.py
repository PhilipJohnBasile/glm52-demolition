#!/usr/bin/env python3
"""CPU-side (parallel to the GPU): pre-stage a DIVERSE, cached bug-set for a deterministic best-of-N
measurement. Each entry = a mutation that COMPILES but breaks a test, with its changed line + failing
tests. Mix of DISCLOSABLE (div_ceil/saturating_sub) and SUBTLE (>/<, ==/!=) so we can report pass-rate
BY CLASS. Writes BUGSET.json. No model needed — pure cargo/git on CPU."""
import subprocess, re, os, json
CS = "/Users/pjb/git/callsieve"
DISCLOSABLE = [(".div_ceil(4)", " / 4"), (".saturating_sub(1)", ".saturating_sub(2)"), (" + 1", " + 2")]
SUBTLE = [(" > ", " < "), (" >= ", " > "), (" == ", " != "), (" < ", " > ")]
SRCS = ["src/query/tokens.rs", "src/query/classify.rs", "src/query/skeleton.rs"]
def sh(c, **k):
    try: return subprocess.run(c, capture_output=True, text=True, **k)
    except Exception: return None
out = []
for cls, muts in (("disclosable", DISCLOSABLE), ("subtle", SUBTLE)):
    for f in SRCS:
        for find, repl in muts:
            wt = f"/tmp/bs_{abs(hash((f,find,repl)))%100000}"
            sh(["git","-C",CS,"worktree","remove","--force",wt]); sh(["git","-C",CS,"worktree","add","-f",wt,"HEAD"])
            p = os.path.join(wt, f); src = open(p).read()
            if find not in src: sh(["git","-C",CS,"worktree","remove","--force",wt]); continue
            i = src.find(find); line = src[:i].count("\n")+1
            open(p,"w").write(src[:i]+repl+src[i+len(find):])
            comp = sh(["cargo","test","--no-run","-q"], cwd=wt, timeout=300)
            if not comp or comp.returncode != 0: sh(["git","-C",CS,"worktree","remove","--force",wt]); continue
            t = sh(["cargo","test","-q"], cwd=wt, timeout=600)
            blob = ((t.stdout or "")+(t.stderr or "")) if t else ""
            fails = re.findall(r"([A-Za-z0-9_:]+) \.\.\. FAILED", blob)[:3]
            sh(["git","-C",CS,"worktree","remove","--force",wt])
            if t and t.returncode != 0 and fails:
                out.append({"class":cls,"file":f,"find":find,"repl":repl,"line":line,"fails":fails})
                print(f"  ✓ [{cls}] {f}:{line} {find!r}->{repl!r}  ({len(fails)} failing)", flush=True)
                break  # one per (class,file) for diversity
json.dump(out, open("BUGSET.json","w"), indent=1)
print(f"\n  BUGSET: {len(out)} bugs cached ({sum(b['class']=='disclosable' for b in out)} disclosable, {sum(b['class']=='subtle' for b in out)} subtle) -> BUGSET.json")
