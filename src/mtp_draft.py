"""#34/#10 — MTP self-speculative draft→verify loop (the algorithm). The model's own MTP head (layer 78,
now downloaded) drafts the next token(s) from the current hidden state; the main model verifies them in one
batched forward; accepted drafts give multiple tokens per forward (~1.3-2x decode, lossless). The accept/
reject logic is GPU-free + testable here; the MTP-head forward + main-model verify are the GPU steps (to be
wired into glm_moe_dsa.py per mlx-lm PR #990 / MTPLX — kept SEPARATE so the live loader isn't touched).
"""
from __future__ import annotations


def accept_drafts(draft_tokens, verify_tokens):
    """Speculative verification (the standard lossless rule): accept the longest prefix of draft_tokens that
    matches the main model's greedy verify_tokens; on the first mismatch, take the main model's token and stop.
    If every draft matched, append the main model's bonus token. Returns (output_tokens, n_drafts_accepted).
    Guarantees the SAME output as plain greedy decoding — the speedup is free."""
    out = []
    for d, v in zip(draft_tokens, verify_tokens):
        if d == v:
            out.append(d)
        else:
            out.append(v)                      # correct with the main model's token, then stop
            return out, len(out) - 1
    if len(verify_tokens) > len(draft_tokens):
        out.append(verify_tokens[len(draft_tokens)])   # bonus token from the verify pass
    return out, len(draft_tokens)


def expected_speedup(accept_rate, k_draft, verify_cost=1.0):
    """Rough decode speedup: drafting k tokens at accept_rate p yields E[tokens] = (1-p^(k+1))/(1-p) per one
    verify forward. Tune k against the model's MEASURED accept_rate once the head is attached."""
    if accept_rate >= 1.0:
        return k_draft + 1
    return ((1 - accept_rate ** (k_draft + 1)) / (1 - accept_rate)) / verify_cost


def best_k(accept_rate, k_max=8):
    """Pick the draft length k that maximizes expected tokens-per-forward for a given accept_rate."""
    return max(range(1, k_max + 1), key=lambda k: expected_speedup(accept_rate, k))


def _selftest():
    assert accept_drafts([5, 6, 7], [5, 6, 7, 8]) == ([5, 6, 7, 8], 3)     # all match + bonus
    assert accept_drafts([5, 6, 7], [5, 9, 7]) == ([5, 9], 1)              # mismatch at 1 → correct + stop
    assert accept_drafts([1], [2]) == ([2], 0)                            # first wrong → 0 accepted
    assert expected_speedup(0.9, 3) > expected_speedup(0.5, 3) > 1.0       # monotonic in accept_rate
    assert expected_speedup(1.0, 4) == 5                                   # perfect drafting → k+1 tokens
    assert 1 <= best_k(0.8) <= 8
    print("  mtp_draft selftest PASS (#34): lossless speculative accept/reject + speedup model + best_k tuner")


if __name__ == "__main__":
    _selftest()
