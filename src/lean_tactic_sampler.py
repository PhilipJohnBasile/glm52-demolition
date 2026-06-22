"""Deep-MLX novel plateau idea — a custom logit-bias sampler that steers Lean proof generation toward the
under-used CLOSING tactics (omega/simp/decide/tauto) the model avoids on arithmetic/logic goals. The
inference-time complement to the training-time enumerate_tactics bootstrap: instead of (or before) brute-
forcing, just NUDGE the model's own logits so it TRIES omega on `0+n=n` itself. Pure MLX — an additive logit
bias on the tactics' first token, applied as an mlx_lm logits_processor. Bias-build + apply are GPU-free +
tested here; the live decode plugs into mlx_lm.generate(..., logits_processors=[proc]).
"""
import mlx.core as mx


def tactic_bias_vector(tokenizer, vocab_size, tactics, boost=2.0):
    """Build an additive logit-bias vector: +boost on the FIRST token of each boost-tactic (across the spacing
    variants a tokenizer might split on). Real use: encode with add_special_tokens=False so ids[0] is the
    tactic, not BOS. Returns mx.array[vocab_size]."""
    import numpy as np
    bias = np.zeros(vocab_size, dtype=np.float32)
    for tac in tactics:
        for variant in (tac, " " + tac, "by " + tac, " by " + tac):
            try:
                ids = tokenizer.encode(variant)
            except Exception:  # noqa: BLE001
                continue
            if ids and 0 <= ids[0] < vocab_size:
                bias[ids[0]] += boost
    return mx.array(bias)


def apply_bias(logits, bias):
    """The MLX way: additive bias before softmax/sampling — lossless to the rest of the distribution, just
    raises the tactics' odds. logits + bias."""
    return logits + bias


def make_logits_processor(bias):
    """mlx_lm-compatible logits_processor (tokens, logits) -> biased logits. Plug into mlx_lm.generate."""
    def proc(tokens, logits):
        return logits + bias
    return proc


def _selftest():
    import numpy as np

    class Tok:
        V = {"omega": [10], " omega": [11], "simp": [12], " simp": [13],
             "by omega": [99, 10], " by omega": [98, 11]}

        def encode(self, s):
            return Tok.V.get(s, [])

    bias = tactic_bias_vector(Tok(), 100, ["omega", "simp"], boost=3.0)
    b = np.array(bias.tolist())
    assert b[10] == 3.0 and b[11] == 3.0 and b[12] == 3.0 and b[13] == 3.0, b[[10, 11, 12, 13]]
    assert b[0] == 0.0                                        # untouched tokens stay unbiased
    out = apply_bias(mx.zeros((100,)), bias)
    assert float(out[10]) == 3.0 and float(out[0]) == 0.0
    assert int(mx.argmax(out).item()) in (10, 11, 12, 13, 98, 99)   # a boosted tactic token now wins
    proc = make_logits_processor(bias)
    assert float(proc(None, mx.zeros((100,)))[12]) == 3.0
    print("  lean_tactic_sampler selftest PASS (deep-MLX): additive logit-bias steers decode toward omega/simp/decide")


if __name__ == "__main__":
    _selftest()
