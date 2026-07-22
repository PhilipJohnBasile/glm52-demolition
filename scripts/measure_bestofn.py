#!/usr/bin/env python3
"""#113 measurement (v2): bestofn_fix over a VERIFIED diverse bug-set. Each mutation actually exists
AND is confirmed to BREAK a test before measuring (else a non-breaking mutation = false PASS). Fresh
worktree per bug (own target). Reports pass-rate BY CLASS + candidates-to-fix — the honest ours-armed
product number."""
import subprocess, re, os, json, time
CS=os.environ.get("CALLSIEVE_REPO", os.path.expanduser("~/git/callsieve"))  # target repo to mutate
GLM=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))          # this repo (scripts/..)
BUGS=[("disclosable","src/query/tokens.rs",".div_ceil(4)"," / 4"),
      ("disclosable","src/query/skeleton.rs"," - 1"," + 1"),
      ("subtle","src/query/skeleton.rs"," > "," < "),
      ("subtle","src/query/classify.rs"," >= "," > "),
      ("subtle","src/query/classify.rs"," == "," != "),
      ("subtle","src/query/classify.rs"," <= "," < ")]
def sh(c,**k):
    try: return subprocess.run(c,capture_output=True,text=True,**k)
    except Exception: return None
res=[]
for cls,f,find,repl in BUGS:
    wt=f"/tmp/mb_{abs(hash((f,find,repl)))%100000}"
    sh(["git","-C",CS,"worktree","remove","--force",wt]); sh(["git","-C",CS,"worktree","add","-f",wt,"HEAD"])
    p=os.path.join(wt,f); src=open(p).read()
    if find not in src: print(f"  skip {f} {find!r} (absent)",flush=True); sh(["git","-C",CS,"worktree","remove","--force",wt]); continue
    i=src.find(find); line=src[:i].count("\n")+1
    open(p,"w").write(src[:i]+repl+src[i+len(find):])
    pre=sh(["cargo","test","-q"],cwd=wt,timeout=600)        # warms target + VERIFIES the bug breaks a test
    if not pre or pre.returncode==0:
        print(f"  skip {f} {find!r}->{repl!r} (compiles+passes — not a real bug)",flush=True)
        sh(["git","-C",CS,"worktree","remove","--force",wt]); continue
    t0=time.time()
    r=sh([".venv/bin/python","scripts/bestofn_fix.py","--repo",wt,"--file",f,"--line",str(line),
          "--n","5","--base-url","http://localhost:8080/v1"],cwd=GLM,timeout=1500)
    dt=round(time.time()-t0); out=(r.stdout or "") if r else ""
    score=sh(["cargo","test","-q"],cwd=wt,timeout=600)
    passed=bool(score and score.returncode==0)
    m=re.search(r"PASS in (\d+) candidate",out); cands=int(m.group(1)) if m else None
    res.append({"class":cls,"bug":f"{f} {find}->{repl}","passed":passed,"cands":cands,"secs":dt})
    print(f"  [{cls}] {f} {find!r}->{repl!r}: {'PASS' if passed else 'FAIL'} cands={cands} {dt}s",flush=True)
    sh(["git","-C",CS,"worktree","remove","--force",wt])
json.dump(res,open("BESTOFN_MEASURE.json","w"),indent=1)
print("\n  === #113 RESULT ===",flush=True)
for cls in ("disclosable","subtle"):
    cr=[r for r in res if r["class"]==cls]
    if cr: print(f"  {cls}: {sum(r['passed'] for r in cr)}/{len(cr)} pass · cands {[r['cands'] for r in cr]}",flush=True)
tot=len(res); print(f"  OVERALL: {sum(r['passed'] for r in res)}/{tot}",flush=True)
