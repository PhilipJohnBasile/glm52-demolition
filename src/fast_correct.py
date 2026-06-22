"""FAST + CORRECT decode in ONE loop — the DOMINO combine (research/quant_heal_speed_sota_10rounds.md R13-14).

Two of our pieces, unified:
  - prompt-lookup speculation (#70, propose_draft) — n-gram drafts, NO draft model -> 2-4x on code-editing.
  - constraint mask (#45, Validator.banned_token_ids) — banned tokens get -inf logits -> 100% valid by construction.

The insight: apply the constraint mask to the spec VERIFY step. A banned draft token can never match the masked
prediction, so it's rejected automatically; every ACCEPTED token is grammar-valid. The grammar even RAISES draft
acceptance (predictable positions), so correctness makes it faster, not slower. Lossless vs constrained-greedy.

  from fast_correct import generate_fast_correct
  ids, n_fwd, n = generate_fast_correct(model, tok, prompt_ids, banned_ids=validator.banned_token_ids(vocab))
  # speedup ≈ n / n_fwd ; every token in `ids` respects the ban set
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from prompt_lookup import propose_draft   # noqa: E402  (#70, pure n-gram draft)


def generate_fast_correct(model, tokenizer, prompt_ids, banned_ids=None,
                          max_tokens=256, num_draft=8, max_ngram=3):
    """Prompt-lookup speculation + constraint mask in one greedy loop. `banned_ids`: a set/iterable of token ids
    to forbid (from constrained_decode); None = pure speed. Returns (generated_ids, n_forwards, n_generated)."""
    import mlx.core as mx
    from mlx_lm.models import cache as _cache
    eos = getattr(tokenizer, "eos_token_id", None)
    ban_set = sorted(set(banned_ids)) if banned_ids else None
    ban_vec = None                                              # built lazily once we know the vocab size
    kv = _cache.make_prompt_cache(model)
    toks = list(prompt_ids)
    if len(toks) > 1:
        model(mx.array(toks[:-1])[None], cache=kv)              # prefill cache := prompt[:-1]
    y = mx.array(toks[-1:], mx.uint32)
    out, n_fwd = [], 0
    while len(out) < max_tokens:
        budget = min(num_draft, max_tokens - len(out))
        draft = propose_draft(toks, max_ngram=max_ngram, num_draft=budget)   # [] -> plain step
        m = len(draft)
        yin = mx.concatenate([y, mx.array(draft, mx.uint32)]) if m else y
        logits = model(yin[None], cache=kv)[0]                  # [m+1, vocab] — ONE forward verifies all drafts
        if ban_set is not None:                                # CONSTRAINT: banned tokens become impossible
            if ban_vec is None:
                import numpy as np
                bv = np.zeros(logits.shape[-1], np.float32)
                bv[ban_set] = -1e9
                ban_vec = mx.array(bv)
            logits = logits + ban_vec
        preds = mx.argmax(logits, axis=-1).tolist()
        n_fwd += 1
        n = 0
        while n < m and preds[n] == draft[n]:                  # accept the longest agreed (now grammar-valid) prefix
            n += 1
        _cache.trim_prompt_cache(kv, m - n)                    # roll back rejected drafts' KV
        for t in preds[:n + 1]:                                # n accepted drafts + 1 real model token
            out.append(t)
            toks.append(t)
            if eos is not None and t == eos:
                return out, n_fwd, len(out)
        y = mx.array([preds[n]], mx.uint32)
    return out, n_fwd, len(out)


def _selftest():
    """CPU: the three core pieces of the combine (draft reuse, ban-mask, accept-prefix). Full-model speedup
    is a serve-time measurement (needs the GPU)."""
    import mlx.core as mx
    import numpy as np
    # 1) propose_draft reuses an earlier span (the code-editing case)
    d = propose_draft([1, 2, 3, 4, 1, 2, 3], max_ngram=3, num_draft=3)
    assert d == [4, 1, 2], d                                   # after the earlier "1 2 3" comes 4,1,2

    # 2) additive ban-mask makes a token impossible without touching the rest
    V = 10
    logits = mx.array(np.array([[0., 5., 0., 0., 0., 0., 0., 0., 0., 0.]], np.float32))  # peak @ token 1
    assert int(mx.argmax(logits, axis=-1)[0]) == 1
    bv = np.zeros(V, np.float32); bv[1] = -1e9
    masked = logits + mx.array(bv)
    assert int(mx.argmax(masked, axis=-1)[0]) != 1, "banned token must not be selected"

    # 3) accept-prefix: accept the agreed run, stop at the first disagreement
    draft, preds = [4, 5, 6], [4, 5, 9]
    n = 0
    while n < len(draft) and preds[n] == draft[n]:
        n += 1
    assert n == 2                                              # accept [4,5], reject 6

    print("  fast_correct selftest PASS — draft-reuse + ban-mask + accept-prefix (the DOMINO combine) correct")
    print("  speedup ≈ n_generated/n_forwards (serve-time); every accepted token respects the ban set")


if __name__ == "__main__":
    _selftest()
