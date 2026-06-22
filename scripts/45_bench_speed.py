#!/usr/bin/env python3
"""Speed benchmark for the Wave-2 levers — a REAL tok/s number, not a guess.
Measures decode tok/s on a fixed set of niche coding prompts, and the speculative
speedup when a draft model is given (mlx_lm's in-process speculative via
stream_generate(draft_model=..., num_draft_tokens=...)).

  # baseline (the current served model)
  python scripts/45_bench_speed.py --model models/GLM-5.2-q3a4-v2 --adapter heal/adapters-grpo
  # speculative with the GLM-4.7-Flash draft (compares vs baseline + reports speedup)
  python scripts/45_bench_speed.py --model models/GLM-5.2-q3a4-v2 --adapter heal/adapters-grpo \
      --draft models/GLM-4.7-Flash-5bit --num-draft-tokens 4
  # active-experts variant: point --model at a num_experts_per_tok=6 copy (scripts/22)

Note: target (~99GB) + draft (~20GB) = ~120GB of 128 — the speculative pass is the
real memory test; if it OOMs, re-quant the draft to 4-bit (scripts/24b) and retry.
"""
import argparse
import time

import mlx.core as mx

PROMPTS = [
    "Write a TypeScript function debounce<T extends (...a:any)=>void>(fn:T, ms:number) with correct types.",
    "Implement a Rust function `nth_fib(n: u64) -> u64` iteratively.",
    "Write a Python function merge_sorted(a, b) that merges two sorted lists.",
    "Write a Go function ReverseString(s string) string that is rune-safe.",
]


def bench(model, tok, draft_model, n_draft, max_tokens):
    from mlx_lm import stream_generate
    ntok = 0
    t0 = time.perf_counter()
    for p in PROMPTS:
        prompt = tok.apply_chat_template(
            [{"role": "user", "content": p}], add_generation_prompt=True,
            tokenize=False, enable_thinking=False)
        kw = {"max_tokens": max_tokens}
        if draft_model is not None:
            kw["draft_model"] = draft_model
            kw["num_draft_tokens"] = n_draft
        last = None
        for resp in stream_generate(model, tok, prompt, **kw):
            last = resp
            ntok += 1
        # mlx_lm's GenerationResponse exposes generation_tps on the final chunk
    dt = time.perf_counter() - t0
    return ntok / dt, ntok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--draft", default=None)
    ap.add_argument("--num-draft-tokens", type=int, default=4)
    ap.add_argument("--max-tokens", type=int, default=200)
    args = ap.parse_args()
    from mlx_lm import load

    model, tok = load(args.model, adapter_path=args.adapter)
    base_tps, n = bench(model, tok, None, 0, args.max_tokens)
    print(f"  baseline           : {base_tps:5.1f} tok/s   ({n} tok over {len(PROMPTS)} prompts)")

    if args.draft:
        try:
            draft, _ = load(args.draft)
        except Exception as e:  # noqa: BLE001
            print(f"  draft load FAILED ({str(e)[:60]}) — likely OOM; re-quant draft to 4-bit")
            return
        try:
            spec_tps, _ = bench(model, tok, draft, args.num_draft_tokens, args.max_tokens)
            sp = spec_tps / base_tps
            verdict = "KEEP draft ✅" if sp > 1.15 else "marginal" if sp > 1.0 else "draft HURTS — drop it"
            print(f"  speculative (k={args.num_draft_tokens:<2}): {spec_tps:5.1f} tok/s   "
                  f"->  {sp:.2f}x   :: {verdict}")
        except Exception as e:  # noqa: BLE001
            print(f"  speculative pass FAILED ({str(e)[:70]}) — 120GB likely OOM; 4-bit draft")


if __name__ == "__main__":
    main()
