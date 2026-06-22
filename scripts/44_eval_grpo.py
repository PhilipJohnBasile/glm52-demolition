#!/usr/bin/env python3
"""GRPO vs SFT — the real proof RL helped: pass-rate on a FIXED task set with the
true verifier (exec_check). Loads the model + each adapter ONE AT A TIME (never
both 99GB in RAM), greedily generates (thinking off), scores with exec_check.check.

  python scripts/44_eval_grpo.py --n 12
"""
import argparse
import gc
import json
import os
import sys

import mlx.core as mx

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from exec_check import check  # noqa: E402


def _prompt(tok, task):
    msgs = [{"role": "user", "content": task["prompt"]}]
    try:
        return tok.apply_chat_template(msgs, add_generation_prompt=True,
                                       tokenize=False, enable_thinking=False)
    except TypeError:                                  # older template without the kwarg
        return tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)


def eval_adapter(model_path, adapter, tasks, max_tokens):
    from mlx_lm import load, generate
    model, tok = load(model_path, adapter_path=adapter)
    npass = ntot = 0
    marks = []
    for t in tasks:
        try:
            out = generate(model, tok, _prompt(tok, t), max_tokens=max_tokens, verbose=False)
        except TypeError:                              # generate API variation
            out = generate(model, tok, prompt=_prompt(tok, t), max_tokens=max_tokens)
        ok = check(t, out)
        marks.append((t.get("id"), ok))
        if ok is not None:
            ntot += 1
            npass += int(bool(ok))
    del model, tok
    gc.collect()
    mx.clear_cache()
    return npass, ntot, marks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--sft", default="heal/adapters")
    ap.add_argument("--grpo", default="heal/adapters-grpo")
    args = ap.parse_args()
    tasks = [json.loads(l) for l in open(os.path.join(HERE, "..", "eval", "tasks.jsonl"))
             if l.strip()][:args.n]
    print(f"  eval {len(tasks)} tasks (greedy, thinking off) — one model at a time\n")
    out = {}
    for label, adapter in [("SFT", args.sft), ("GRPO", args.grpo)]:
        if not os.path.exists(os.path.join(adapter, "adapters.safetensors")):
            print(f"  {label}: adapter missing ({adapter}) — skip")
            continue
        p, tot, marks = eval_adapter(args.model, adapter, tasks, args.max_tokens)
        out[label] = (p, tot)
        pct = 100 * p // max(tot, 1)
        print(f"  {label:5} pass {p}/{tot}  ({pct}%)  "
              f"[{adapter}]")
    if "SFT" in out and "GRPO" in out:
        (sp, st), (gp, gt) = out["SFT"], out["GRPO"]
        d = (100 * gp // max(gt, 1)) - (100 * sp // max(st, 1))
        verdict = ("GRPO IMPROVED correctness ✅" if d > 0 else
                   "no gain (tie)" if d == 0 else "GRPO regressed — revert to SFT")
        print(f"\n  SFT {sp}/{st} vs GRPO {gp}/{gt}  ->  {d:+d} pts  ::  {verdict}")


if __name__ == "__main__":
    main()
