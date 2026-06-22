"""#115 Prompt-lookup speculative decoding — beat the decode bandwidth ceiling for CODE.

mlx-lm's `speculative_generate_step` needs a draft MODEL (a forward pass per draft token). For code the
output mostly REUSES the input — a fix is the buggy function with a few edits — so we can draft for FREE:
take the current suffix, find that n-gram earlier in the prompt+generation, and copy what followed it.
No draft model, no extra weights. The big model then verifies all K drafts in ONE forward pass; every
accepted draft is a token produced without an extra weight-read → that's the only honest way past the
memory-bandwidth ceiling (#81/#117 confirmed standard decode can't be sped up; this can).

Greedy spec-decode is EXACT: output is token-identical to plain greedy. The self-test asserts that, then
measures the speedup. Reuses mlx-lm's cache-rewind contract (trimmable prompt cache).

  python src/spec_decode.py --selftest    # loads the model — run during a serve-stop, NEVER vs the flywheel
"""
import sys
import time

import mlx.core as mx
from mlx_lm.models import cache


def ngram_draft(toks, n_gram, num_draft):
    """Most-recent-occurrence n-gram lookup: find the last suffix match, return what followed it."""
    if len(toks) < n_gram + 1:
        return []
    suffix = toks[-n_gram:]
    for i in range(len(toks) - n_gram - 1, -1, -1):
        if toks[i:i + n_gram] == suffix:
            return toks[i + n_gram: i + n_gram + num_draft]
    return []


def prompt_lookup_generate_step(prompt, model, *, n_gram=3, num_draft_tokens=8, max_tokens=256,
                                sampler=None, prompt_cache=None):
    """Yield (token, n_accepted) — n_accepted>0 means draft tokens were free that step."""
    sampler = sampler or (lambda x: mx.argmax(x, axis=-1))
    model_cache = prompt_cache if prompt_cache is not None else cache.make_prompt_cache(model)
    if not cache.can_trim_prompt_cache(model_cache):
        raise ValueError("prompt-lookup needs a trimmable prompt cache")

    all_tokens = prompt.tolist()
    y = prompt.astype(mx.uint32)

    def _logits(yv, n_predict):
        out = model(yv[None], cache=model_cache)[:, -n_predict:, :]
        return sampler(out.squeeze(0)).tolist()          # argmax token per position

    # prefill the prompt (leave the last token to seed generation)
    while y.size > 1:
        n = min(512, y.size - 1)
        model(y[:n][None], cache=model_cache)
        mx.eval([c.state for c in model_cache])
        y = y[n:]

    ntoks = 0
    while ntoks < max_tokens:
        draft = ngram_draft(all_tokens, n_gram, min(num_draft_tokens, max_tokens - ntoks - 1))
        num_draft = len(draft)
        yv = mx.concatenate([y, mx.array(draft, mx.uint32)]) if num_draft else y
        toks = _logits(yv, num_draft + 1)                 # model's argmax at each of num_draft+1 positions
        # accept the run of drafts the model agrees with, then its (correcting/bonus) token
        n = 0
        while n < num_draft and toks[n] == draft[n]:
            all_tokens.append(toks[n]); yield toks[n], 1; ntoks += 1; n += 1
            if ntoks >= max_tokens:
                break
        if ntoks < max_tokens:
            all_tokens.append(toks[n]); yield toks[n], 0; ntoks += 1
        cache.trim_prompt_cache(model_cache, num_draft - n)   # drop KV of rejected drafts
        y = mx.array([toks[n]], mx.uint32)


def _selftest():
    from mlx_lm import load
    model_path = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "models/GLM-5.2-q3a4-v2"
    print(f"  loading {model_path} ...")
    model, tok = load(model_path)
    # a code-fix prompt: the output reuses the buggy code (ideal for prompt-lookup)
    prompt = ("Fix the bug and output the corrected Python function only:\n"
              "def add(a, b):\n    return a - b\n")
    ids = mx.array(tok.encode(prompt))
    MAXT = 80

    # 1) correctness: prompt-lookup greedy must equal plain greedy
    pl = [t for t, _ in zip((tt for tt, _ in prompt_lookup_generate_step(ids, model, max_tokens=MAXT)), range(MAXT))]
    from mlx_lm.generate import generate_step
    base = [t for (t, _), _ in zip(generate_step(ids, model, max_tokens=MAXT), range(MAXT))]
    identical = pl == base
    print(f"  correctness (prompt-lookup == greedy): {'✅ IDENTICAL' if identical else '❌ DIVERGED'}")

    # 2) speed: tokens vs forward passes (acceptance) + wall-clock both ways
    t0 = time.time(); acc = 0; n = 0
    for _, a in prompt_lookup_generate_step(ids, model, max_tokens=MAXT):
        acc += a; n += 1
    pl_dt = time.time() - t0
    t0 = time.time()
    for _, _ in zip(generate_step(ids, model, max_tokens=MAXT), range(MAXT)):
        pass
    base_dt = time.time() - t0
    print(f"  drafted-accepted: {acc}/{n} tokens free · wall-clock {base_dt:.1f}s → {pl_dt:.1f}s "
          f"({base_dt / max(pl_dt, 1e-9):.2f}× on this code prompt)")
    print("  ✅ #115 prompt-lookup spec-decode validated" if identical else "  ⚠️ needs fix")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        print(__doc__)
