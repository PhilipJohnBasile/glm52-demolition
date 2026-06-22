#!/usr/bin/env python3
"""#114 (feasible): distill verifier-gated best-of-N INTO the weights. Loop synthetic bugs -> bestofn_fix
-> keep ONLY cargo-verified-correct fixes -> save (fix-packet prompt -> correct apply_patch) as SFT data.
The 'teacher' is best-of-N+verifier (provably better than single-shot, the √H result); SFT distills it
into the student so it one-shots next time (recovers accuracy AND speed). No FP teacher, crash-safe."""
import subprocess, re, os, json, time, sys
CS="/Users/pjb/git/callsieve"; GLM="/Users/pjb/git/glm52-demolition"
OUT=os.path.join(GLM,"recover_data.jsonl")
# real, test-breaking mutations (from the file-scan): disclosable + subtle, across files
BUGS=[("src/query/tokens.rs",".div_ceil(4)"," / 4"),("src/query/skeleton.rs"," > "," < "),
      ("src/query/skeleton.rs"," - 1"," + 1"),("src/query/classify.rs"," >= "," > ")]
def sh(c,**k):
    try: return subprocess.run(c,capture_output=True,text=True,**k)
    except Exception: return None
rounds=int(sys.argv[1]) if len(sys.argv)>1 else 3
kept=0
for rnd in range(rounds):
  for f,find,repl in BUGS:
    wt=f"/tmp/rd_{abs(hash((f,find,rnd)))%100000}"
    sh(["git","-C",CS,"worktree","remove","--force",wt]); sh(["git","-C",CS,"worktree","add","-f",wt,"HEAD"])
    p=os.path.join(wt,f); src=open(p).read()
    if find not in src: sh(["git","-C",CS,"worktree","remove","--force",wt]); continue
    i=src.find(find); line=src[:i].count("\n")+1
    mutated=src[:i]+repl+src[i+len(find):]
    open(p,"w").write(mutated)
    buggy=mutated.split("\n")[line-1]   # the MUTATED (buggy) line the model actually sees
    pre=sh(["cargo","test","-q"],cwd=wt,timeout=600)
    if not pre or pre.returncode==0: sh(["git","-C",CS,"worktree","remove","--force",wt]); continue
    r=sh([".venv/bin/python","scripts/bestofn_fix.py","--repo",wt,"--file",f,"--line",str(line),
          "--n","6","--base-url","http://localhost:8080/v1"],cwd=GLM,timeout=1500)
    out=(r.stdout or "") if r else ""
    m=re.search(r"applied '(.+)'\s*$",out.strip().splitlines()[-1]) if "PASS" in out else None
    fixed=open(p).read().split("\n")[line-1] if "PASS in" in out else None
    if fixed and fixed.strip()!=buggy.strip():
        # SFT example: fix-packet prompt -> the correct one-line apply_patch
        ctx="\n".join(open(p).read().split("\n")[max(0,line-4):line+2])
        prompt=(f"Fix the bug. {f} line {line} is `{buggy.strip()}`. Context:\n```rust\n{ctx}\n```\n"
                f"Output the corrected line {line} (valid Rust, one line).")
        ex={"messages":[{"role":"user","content":prompt},{"role":"assistant","content":fixed.strip()}]}
        with open(OUT,"a") as w: w.write(json.dumps(ex)+"\n"); kept+=1
        print(f"  ✓ kept verified fix: {buggy.strip()!r} -> {fixed.strip()!r} (total {kept})",flush=True)
    sh(["git","-C",CS,"worktree","remove","--force",wt])
print(f"\n  RECOVER_DATA: {kept} verified-correct fixes -> recover_data.jsonl (SFT corpus for #114)",flush=True)
