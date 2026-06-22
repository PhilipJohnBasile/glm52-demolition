#!/usr/bin/env python3
"""#114 DIVERSE corpus — CONCURRENT best-of-N (the serve batches → ~5× faster). MBPP + HumanEval canonical
solutions → inject a test-breaking bug → concurrent best-of-N fix → verify with the REAL test → keep
verified, with the failing-test diag in the prompt (fix-packet++). --selftest = CPU pipeline check."""
import json, os, re, sys, urllib.request, concurrent.futures as cf
sys.path.insert(0, "src")
from verifiers import verify
from datasets import load_dataset

MUTS = [(" + 1"," - 1"),(" - 1"," + 1"),(" < "," <= "),(" <= "," < "),(" > "," >= "),(" >= "," > "),
        (" == "," != "),(" != "," == "),(" and "," or "),(" or "," and "),("+= ","-= "),("-= ","+= "),
        ("min(","max("),("max(","min("),(" not "," "),("return ","return not "),
        # NEW families beyond operator-flips (real-bug diversity — the generalization lever):
        ("range(1, ","range(0, "),("range(0, ","range(1, "),  # loop boundary / off-by-one
        ("[1:]","[:]"),("[:-1]","[:]"),("[0]","[1]"),("[-1]","[0]"),  # slicing / indexing off-by-one
        (" + 1)"," )"),(" - 1)"," )"),  # off-by-one in expressions
        ("return True","return False"),("return False","return True"),  # return-literal
        (" * "," + "),(" // "," / "),(" % "," // ")]  # arithmetic-operator family

def gen(prompt, temp):
    b = json.dumps({"messages":[{"role":"user","content":prompt}],"max_tokens":500,"temperature":temp,
                    "top_p":0.95,"chat_template_kwargs":{"enable_thinking":False}}).encode()
    r = urllib.request.Request("http://localhost:8080/v1/chat/completions", b, {"content-type":"application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=180).read())["choices"][0]["message"].get("content") or ""

def extract(t):
    m = re.search(r"```(?:python)?\n(.*?)```", t, re.S); return m.group(1).strip() if m else t.strip()

def problems():
    for ex in load_dataset("google-research-datasets/mbpp","full",split="test"):
        yield (ex["code"], "\n".join(ex["test_list"]), f"mbpp{ex['task_id']}")
    for ex in load_dataset("openai/openai_humaneval", split="test"):
        yield (ex["prompt"]+ex["canonical_solution"], ex["test"]+f"\ncheck({ex['entry_point']})", f"he{ex['task_id']}")

def main():
    selftest = "--selftest" in sys.argv; N = 5
    target = int([a for a in sys.argv[1:] if a.isdigit()][0]) if any(a.isdigit() for a in sys.argv[1:]) else 300
    out = open("recover_data_diverse.jsonl","a") if not selftest else None
    kept = 0
    for code, tests, pid in problems():
        try:
            if not verify("python", code, harness=tests).passed: continue
            bugs = []                                   # MULTIPLE bugs per problem (up to 3) = the multiplier
            for find,repl in MUTS:
                if find in code and len(bugs) < 3:
                    cand = code.replace(find,repl,1); v = verify("python", cand, harness=tests)
                    if not v.passed: bugs.append((find,repl,cand,v.diag))
            if not bugs: continue
            if selftest:
                kept+=1; print(f"  ✓ {pid}: {len(bugs)} real bugs", flush=True)
                if kept>=6: print("  SELFTEST OK"); return
                continue
            for find,repl,buggy,diag in bugs:
                prompt = (f"This Python code has a bug — the test fails:\n```python\n{buggy}\n```\n"
                          f"Failing test output:\n{(diag or '')[:400]}\nTests:\n```python\n{tests}\n```\n"
                          f"Output ONLY the corrected full code.")
                with cf.ThreadPoolExecutor(max_workers=N) as ex:    # CONCURRENT best-of-N (serve batches)
                    cands = list(ex.map(lambda i: extract(gen(prompt, 0.4+0.12*i)), range(N)))
                for c in cands:
                    if c and c.strip()!=buggy.strip() and verify("python", c, harness=tests).passed:
                        out.write(json.dumps({"messages":[{"role":"user","content":prompt},{"role":"assistant","content":c}]})+"\n"); out.flush()
                        kept+=1; print(f"  ✓ kept {pid} {find!r}->{repl!r} (total {kept})", flush=True); break
                if kept>=target: break
            if kept>=target: break
        except Exception as e:
            print(f"  ! {pid} error: {type(e).__name__}", flush=True); continue
    print(f"\n  DIVERSE CORPUS: {kept} verified fixes -> recover_data_diverse.jsonl")

if __name__=="__main__": main()
