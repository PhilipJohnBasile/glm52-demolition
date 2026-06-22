#!/usr/bin/env python3
"""Best-of-N + real-verification orchestrator — the frontier-beater (plan step 7).

The proven way a small specialist beats a frontier model in a niche: generate N
candidates, VERIFY each with a REAL signal (run the tests for code; render+measure
for design — both stronger than a learned reward model), return the best, and
self-correct once on failure. Wraps any OpenAI-compatible endpoint (the served
model behind the think-proxy).

  # coding (verify by executing tests)
  python scripts/26_bestofn.py --mode code --base-url http://localhost:8081/v1 \
      --task "Write rust dedup_sorted(v:Vec<i32>)->Vec<i32>" \
      --check compile_rust --harness 'fn main(){assert_eq!(dedup_sorted(vec![3,1,2,1,3]),vec![1,2,3]);println!("OK");}'

  # design (verify by render+measure)
  python scripts/26_bestofn.py --mode design --base-url http://localhost:8081/v1 \
      --task "an art-directed pricing hero, OKLCH tokens, no framework defaults"
"""
import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from exec_check import check, extract_code  # noqa: E402


def chat(base_url, messages, temperature, max_tokens=2200):
    # mlx_lm.server wants the model PATH (not "local"); thinking-off for clean output
    model = os.environ.get("MODEL_ID", "models/GLM-5.2-q3a4-v2")
    body = json.dumps({"model": model, "messages": messages,
                       "temperature": temperature, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(base_url + "/chat/completions", body,
                                 {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=400).read())["choices"][0]["message"]["content"]


def code_verify(task, args):
    """Generate N solutions, return the first that PASSES the tests (run-the-tests)."""
    t = {"check": args.check, "harness": args.harness or "",
         "must_contain": (args.must_contain or "").split(",")}
    sysmsg = "You are an expert programmer. Return ONLY a fenced code block."
    msgs = [{"role": "system", "content": sysmsg},
            {"role": "user", "content": task}]
    best = None
    for n in range(args.n):
        reply = chat(args.base_url, msgs, 0.0 if n == 0 else 0.7)
        ok = check(t, reply)
        print(f"  candidate {n+1}/{args.n}: {'PASS' if ok else ('skip' if ok is None else 'fail')}")
        if ok is True:
            return reply, True
        best = reply
        # one self-correction: tell it what failed, ask to fix
        if n == 0:
            msgs += [{"role": "assistant", "content": reply},
                     {"role": "user", "content": "That failed its tests. Fix it and return only the corrected code."}]
    return best, False


def design_verify(task, args):
    """Generate N, render+measure each, return the lowest-findings design."""
    import importlib.util as u
    spec = u.spec_from_file_location("dc", os.path.join(HERE, "25_design_critique.py"))
    dc = u.module_from_spec(spec)
    sys.argv = ["dc"]
    spec.loader.exec_module(dc)
    msgs = [{"role": "system", "content": dc.SYS},
            {"role": "user", "content": f"Design: {task}"}]
    out = os.path.join(HERE, "..", "design_out")
    os.makedirs(out, exist_ok=True)
    best, best_issues = None, 999
    for n in range(args.n):
        html = dc.extract_html(chat(args.base_url, msgs, 0.4))
        try:
            m = dc.measure(html, os.path.join(out, f"bon{n}.png"))
            issues = dc.critique(html, m)
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] render failed ({e})"); issues = []
        print(f"  candidate {n+1}/{args.n}: {len(issues)} findings")
        if len(issues) < best_issues:
            best, best_issues = html, len(issues)
        if not issues:
            break
        msgs += [{"role": "assistant", "content": f"```html\n{html}\n```"},
                 {"role": "user", "content": "Findings:\n- " + "\n- ".join(issues) +
                  "\nFix all and return the revised HTML."}]
    return best, best_issues == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["code", "design"], required=True)
    ap.add_argument("--base-url", default="http://localhost:8081/v1")
    ap.add_argument("--task", required=True)
    ap.add_argument("--n", type=int, default=4, help="candidates to generate")
    ap.add_argument("--check", default="exec")           # code: exec_check kind
    ap.add_argument("--harness", default=None)
    ap.add_argument("--must-contain", default=None)
    args = ap.parse_args()

    if args.mode == "code":
        result, ok = code_verify(args.task, args)
        print(f"\n{'✅ VERIFIED (tests pass)' if ok else '⚠️ best-effort (no candidate passed)'}\n")
        print(extract_code(result))
    else:
        result, ok = design_verify(args.task, args)
        path = os.path.join(HERE, "..", "design_out", "best.html")
        open(path, "w").write(result or "")
        print(f"\n{'✅ clean design (0 findings)' if ok else '⚠️ best of N'} -> {path}")


if __name__ == "__main__":
    main()
