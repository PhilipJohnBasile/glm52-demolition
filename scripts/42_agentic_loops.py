#!/usr/bin/env python3
"""Thicken agentic data with REAL edit->check->fix loops (plan #9). Our heal data
is single-shot completions; an agent must write code, READ the toolchain's actual
error, and fix it. Each exercise here injects a real bug, runs the REAL verifier
(scripts/30) to capture the authentic diagnostic, and emits a trajectory:
  user(task) -> assistant(buggy) -> user(real toolchain error) -> assistant(fixed)
so the model learns the loop, grounded in true compiler output (not invented).

  python scripts/42_agentic_loops.py
-> heal/mine/agentic_loops.jsonl
"""
import importlib.util as iu
import json
import os
import sys

HERE = os.path.dirname(__file__)


def _load(path):
    spec = iu.spec_from_file_location(os.path.basename(path)[:-3], path)
    m = iu.module_from_spec(spec)
    saved = sys.argv
    sys.argv = [path]
    try:
        spec.loader.exec_module(m)
    finally:
        sys.argv = saved
    return m


VR = _load(os.path.join(HERE, "30_verify_repair.py"))

SYS = ("You are an agentic coding assistant. Write code, run the project's checks, "
       "read the toolchain's actual errors, and fix until it passes. Prefer the "
       "compiler/type-checker's feedback over guessing.")

# each: a plausible buggy attempt the REAL verifier rejects, and the fix it accepts
EXERCISES = [
    {"lang": "ts",
     "task": "Write clamp(n:number,min:number,max:number):number that bounds n to [min,max].",
     "buggy": "function clamp(n: number, min: number, max: number): number {\n"
              "  return Math.max(min, Math.min(max, n)).toFixed(2);\n}",
     "fixed": "function clamp(n: number, min: number, max: number): number {\n"
              "  return Math.max(min, Math.min(max, n));\n}"},
    {"lang": "ts",
     "task": "Write sum(xs:number[]):number returning the total.",
     "buggy": "function sum(xs: number[]): number {\n"
              "  return xs.reduce((a, b) => a + total, 0);\n}",
     "fixed": "function sum(xs: number[]): number {\n"
              "  return xs.reduce((a, b) => a + b, 0);\n}"},
    {"lang": "rust",
     "task": "Write pub fn double(x:i32)->i32 returning x*2.",
     "buggy": "pub fn double(x: i32) -> i32 { x * 2.0 }",
     "fixed": "pub fn double(x: i32) -> i32 { x * 2 }"},
    {"lang": "python",
     "task": "Write add(a:int,b:int)->int returning their sum.",
     "buggy": "def add(a: int, b: int) -> int:\n    return a + str(b)",
     "fixed": "def add(a: int, b: int) -> int:\n    return a + b"},
    {"lang": "go",
     "task": "Write add(a,b int) int in package main.",
     "buggy": "package main\nfunc add(a int, b int) int {\n\treturn a + b\n",
     "fixed": "package main\nfunc add(a int, b int) int {\n\treturn a + b\n}"},
    {"lang": "js",
     "task": "Write f(x) that returns x doubled element-wise.",
     "buggy": "function f(x) {\n  return x.map(i => i * 2\n}",
     "fixed": "function f(x) {\n  return x.map(i => i * 2);\n}"},
]


def main():
    rows, skipped = [], 0
    for ex in EXERCISES:
        verify = VR.VERIFIERS.get(ex["lang"])
        if not verify:
            skipped += 1
            continue
        ok_bad, diag = verify(ex["buggy"], "")
        ok_fix, _ = verify(ex["fixed"], "")
        if ok_bad is not False or ok_fix is not True:
            # the exercise didn't behave as designed on this machine's toolchain
            print(f"  [skip] {ex['lang']}: buggy_ok={ok_bad} fixed_ok={ok_fix}")
            skipped += 1
            continue
        rows.append({"messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content": ex["task"]},
            {"role": "assistant", "content": f"```{ex['lang']}\n{ex['buggy']}\n```"},
            {"role": "user", "content": "I ran the checks and they failed:\n```\n"
                                        f"{diag[:700]}\n```\nFix it and return only the code."},
            {"role": "assistant", "content": f"```{ex['lang']}\n{ex['fixed']}\n```"}]})
        print(f"  ✓ {ex['lang']}: real diagnostic captured ({diag[:48].strip()}…)")
    out = os.path.join(HERE, "..", "heal", "mine", "agentic_loops.jsonl")
    with open(out, "w") as f:
        f.write("\n".join(json.dumps(r) for r in rows))
    print(f"\n  {len(rows)} agentic edit->check->fix trajectories -> {out} "
          f"({skipped} skipped). Add to 27_build_heal_data for the next heal.")


if __name__ == "__main__":
    main()
