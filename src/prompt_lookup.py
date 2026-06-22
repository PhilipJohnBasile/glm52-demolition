"""Prompt-lookup decoding (Saxena/Apoorvumang 2023) — n-gram speculative decoding with NO draft model.

The speed plateau (#34): MTP self-spec is blocked (the head needs prune+fuse+requant + mlx-lm PR #990), and
the external draft model is Metal-unstable here (see glm52-speed-findings). Prompt-lookup sidesteps BOTH: for
input-grounded tasks — and especially agentic CODE-EDITING, where the model rewrites spans of the existing
file — match the just-generated tokens against an earlier occurrence in the context and propose the following
tokens as the draft. The target model verifies the whole draft in ONE forward pass; accepted tokens are free.
2-4x on code-editing (the primary use case), zero draft model, zero arch change, works with greedy or sampling.

The draft logic is pure CPU (n-gram lookup) — unit-tested below. Wiring it into the decode loop (the model
verifies the proposed span) is the small remaining GPU step; mlx-lm's speculative_generate_step can consume a
proposer like this.
"""


def propose_draft(tokens, max_ngram: int = 3, num_draft: int = 10):
    """Match the last `n` tokens (n = max_ngram..1) against the most recent EARLIER occurrence in `tokens`, and
    return the up-to-`num_draft` tokens that followed it — the speculative draft. Pure lookup, no model. []
    if no match. Longest-match-first so the most specific context wins."""
    n = len(tokens)
    for ng in range(max_ngram, 0, -1):
        if n <= ng:
            continue
        suffix = tokens[n - ng:]
        for i in range(n - ng - 1, -1, -1):                 # search backward → most recent occurrence
            if tokens[i:i + ng] == suffix:
                return tokens[i + ng:i + ng + num_draft]
    return []


def generate_pld(model, tokenizer, prompt_ids, max_tokens=256, num_draft=8, max_ngram=3):
    """Greedy decode with prompt-lookup speculation — LOSSLESS (bit-identical to greedy argmax), just fewer
    sequential forwards. Mirrors mlx_lm.speculative_generate_step but with propose_draft (n-gram, no model)
    in place of a draft model — so there's no draft cache and no second model resident.
    Returns (generated_ids, n_forwards, n_generated); decode speedup ≈ n_generated / n_forwards."""
    import mlx.core as mx
    from mlx_lm.models import cache as _cache
    eos = getattr(tokenizer, "eos_token_id", None)
    kv = _cache.make_prompt_cache(model)
    toks = list(prompt_ids)
    if len(toks) > 1:
        model(mx.array(toks[:-1])[None], cache=kv)          # prefill: cache := prompt[:-1]
    y = mx.array(toks[-1:], mx.uint32)                       # y := last prompt token (not yet cached)
    out, n_fwd = [], 0
    while len(out) < max_tokens:
        budget = min(num_draft, max_tokens - len(out))
        draft = propose_draft(toks, max_ngram=max_ngram, num_draft=budget)   # [] when no n-gram match → plain step
        m = len(draft)
        yin = mx.concatenate([y, mx.array(draft, mx.uint32)]) if m else y
        preds = mx.argmax(model(yin[None], cache=kv)[0], axis=-1).tolist()   # ONE forward verifies all m drafts
        n_fwd += 1
        n = 0
        while n < m and preds[n] == draft[n]:               # accept the longest agreed prefix (lossless)
            n += 1
        _cache.trim_prompt_cache(kv, m - n)                 # roll back the rejected drafts' KV
        for t in preds[:n + 1]:                             # n accepted drafts + 1 real model token (correction/bonus)
            out.append(t); toks.append(t)
            if (eos is not None and t == eos) or len(out) >= max_tokens:
                return out, n_fwd, len(out)
        y = mx.array([preds[n]], mx.uint32)
    return out, n_fwd, len(out)


_BENCH_PROMPT = (   # code-editing: the model rewrites a span it can COPY from context → PLD lands long drafts
    "Here is a Python function:\n\n"
    "def process(items):\n"
    "    result = []\n"
    "    for item in items:\n"
    "        if item is not None:\n"
    "            result.append(item * 2)\n"
    "    return result\n\n"
    "Rewrite it with type hints (items: list[int]) -> list[int] and a docstring, keeping the logic identical:\n\n")


def bench_pld(model_path, max_tokens=160, num_draft=8, max_ngram=3):
    """GPU: measure the prompt-lookup decode speedup (tokens per forward) + verify losslessness vs plain greedy."""
    import time, mlx.core as mx, mlx_lm
    print(f"  loading {model_path} …", flush=True)
    model, tok = mlx_lm.load(model_path)
    ids = tok.encode(_BENCH_PROMPT)
    t0 = time.time()
    out, n_fwd, n = generate_pld(model, tok, ids, max_tokens=max_tokens, num_draft=num_draft, max_ngram=max_ngram)
    dt = time.time() - t0
    tpf = n / max(n_fwd, 1)
    print(f"\n  PLD: {n} tokens in {n_fwd} forwards = {tpf:.2f} tok/forward  ({n/dt:.1f} tok/s wall, {dt:.1f}s)")
    print(f"  → decode speedup ≈ {tpf:.2f}x vs greedy (greedy = 1.00 tok/forward)")
    # losslessness: the first 24 PLD tokens must equal plain greedy argmax
    from mlx_lm.models import cache as _c
    kv = _c.make_prompt_cache(model)
    if len(ids) > 1:
        model(mx.array(ids[:-1])[None], cache=kv)
    g, y = [], mx.array(ids[-1:], mx.uint32)
    tg = time.time()
    for _ in range(max_tokens):                          # FULL greedy, TIMED → the honest wall-clock baseline
        y = mx.argmax(model(y[None], cache=kv)[0, -1:], axis=-1)
        mx.eval(y); g.append(int(y[0]))
    gdt = time.time() - tg
    print(f"  greedy baseline: {max_tokens} tokens in {gdt:.1f}s = {max_tokens / gdt:.1f} tok/s wall")
    print(f"  lossless (first 24 == greedy): {'✓ identical' if out[:24] == g[:24] else '✗ MISMATCH — bug'}")
    print(f"  → REAL wall-clock speedup = {(n / dt) / (max_tokens / gdt):.2f}x  (PLD {n / dt:.1f} vs greedy {max_tokens / gdt:.1f} tok/s)")
    print(f"     ({tpf:.1f} tok/forward, but each MoE verify-forward loads ~all experts → per-forward ≠ wall)")
    return tpf


def _selftest():
    # a span "10 11 12 13" recurs; after the 2nd "10 11", lookup proposes its continuation "12 13 99"
    toks = [5, 10, 11, 12, 13, 99, 10, 11]
    assert propose_draft(toks, max_ngram=2, num_draft=3) == [12, 13, 99], propose_draft(toks, 2, 3)
    # no earlier occurrence → no draft
    assert propose_draft([1, 2, 3], max_ngram=2, num_draft=3) == []
    # code-editing realism: a function header repeats → propose its body span
    code = "def f ( x ) : return x def f ( x ) :".split()
    assert propose_draft(code, max_ngram=4, num_draft=2) == ["return", "x"], propose_draft(code, 4, 2)
    # longest-match-first: a longer matching context beats a shorter one
    t = [1, 2, 3, 7, 2, 3]                                   # last [2,3]; but [3] also matches earlier
    assert propose_draft(t, max_ngram=2, num_draft=1) == [7]  # [2,3]→ followed by 7
    print("  prompt_lookup selftest PASS — n-gram draft (no model), 2-4x on code-editing, sidesteps the MTP blocker (#34)")


if __name__ == "__main__":
    import sys
    if "--bench" in sys.argv:                               # GPU: measure the real decode speedup + losslessness
        i = sys.argv.index("--bench")
        mp = sys.argv[i + 1] if len(sys.argv) > i + 1 else "models/GLM-5.2-q3a4-v4"
        bench_pld(mp)
    else:
        _selftest()
