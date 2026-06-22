"""#17 design-soul — the DEEPEST activation: mechanistic steering of the residual stream (ActAdd / Representation
Engineering, Zou et al. 2023; Contrastive Activation Addition, Rimsky et al. 2024).

The art/design heritage (Rams, Swiss, Albers, Bauhaus) is encoded in the weights but LATENT. The activation
spectrum, shallow → deep:
  0. PROMPT naming ("Swiss style")            — weak token-level activation (the CANON does this)
  1. DENSE semantic priming (names+era+type)  — floods the context toward the art subspace
  2. FEW-SHOT exemplars (the gold seeds)       — in-context pattern-match, far stronger than description
  3. PERSONA ("you are Müller-Brockmann")      — role-conditions the whole distribution
  4. ACTIVATION STEERING  ← THIS FILE          — inject the "elite" DIRECTION into the residual stream during
       the forward pass, so even a GENERIC prompt yields elite output. Bypasses prompting entirely.
  5. HEAL (weights)                            — SFT on elite-bespoke bakes the same direction permanently.

The steering vector and the heal are two views of ONE thing: move the model onto the elite-art manifold —
transiently (4, a vector added at inference) or permanently (5, folded into the weights by the flywheel).
For a MoE there are TWO injection sites (see `ExpertSteer` note): the residual stream AND the router.

GPU-free: the vector math + injection logic is unit-tested below with mock activations. Capturing real
activations + generating steered needs the model (GPU) — runs after miniF2F.
"""
import mlx.core as mx
import mlx.nn as nn


def steering_vector(elite_acts: mx.array, generic_acts: mx.array) -> mx.array:
    """The 'elite design' DIRECTION in activation space = mean(elite residual) − mean(generic residual),
    unit-normalized. elite_acts/generic_acts are [N, d] mean-pooled residual-stream activations at one layer,
    captured by running the model on elite-bespoke vs cookie-cutter designs (the same contrast the gate enforces)."""
    v = elite_acts.mean(axis=0) - generic_acts.mean(axis=0)
    return v / (mx.linalg.norm(v) + 1e-8)


def inject(h: mx.array, v: mx.array, alpha: float = 6.0) -> mx.array:
    """Add the steering direction to the residual stream: h ← h + α·‖h‖·v. Scaling by the per-token activation
    norm ‖h‖ keeps the nudge proportional across layers/positions (stable). Hook this after a mid/late decoder
    layer in glm_moe_dsa's forward. α≈4–10 typical; too high → degenerate, too low → no effect (sweep it)."""
    scale = mx.linalg.norm(h, axis=-1, keepdims=True)
    return h + alpha * scale * v


# ── MoE-specific DEEPEST activation (note for the GPU pass) ──────────────────────────────────────────────
# Our model is MoE (77 pruned experts). Beyond the residual stream, the ROUTER is a second steering site: if a
# subset of experts encode the aesthetic/design knowledge, add a bias to their router logits (like the Lean
# tactic logit-bias, but on expert selection) → activate the "design experts" directly. Identify them by which
# experts fire most on the elite seeds vs generic (gather router probs over both sets; the high-elite/low-generic
# experts are the aesthetic ones). This is novel + MoE-native; residual steering (above) is the model-agnostic core.


class _SteeredLayer(nn.Module):
    """Wraps a decoder layer; injects the steering direction into its residual-stream output — the rung-4 hook."""
    def __init__(self, inner, v, alpha):
        super().__init__()
        self.inner = inner
        self.steer = v
        self.alpha = alpha

    def __call__(self, *a, **k):
        out = self.inner(*a, **k)
        if isinstance(out, tuple):
            return (inject(out[0], self.steer, self.alpha), *out[1:])   # glm_moe_dsa layers return (h, shared_topk)
        return inject(out, self.steer, self.alpha)


def apply_steering(model, layer_idx: int, v: mx.array, alpha: float = 6.0):
    """WIRE the steering hook into the loaded model's forward at `layer_idx` — opt-in at runtime, does NOT modify
    the published glm_moe_dsa loader. After mlx_lm.load: `remove = apply_steering(model, 40, v)`; remove() undoes it.
    Best at a mid/late layer (~⅔ depth) where the residual carries the semantic direction. α≈4–10 (sweep it)."""
    layers = model.model.layers
    orig = layers[layer_idx]
    layers[layer_idx] = _SteeredLayer(orig, v, alpha)
    return lambda: layers.__setitem__(layer_idx, orig)


def _selftest():
    mx.random.seed(0)
    d = 64
    elite_dir = mx.random.normal((d,))
    elite_dir = elite_dir / mx.linalg.norm(elite_dir)               # the (hidden) true "elite" direction
    elite = elite_dir + 0.15 * mx.random.normal((24, d))            # elite designs cluster near it
    generic = -elite_dir + 0.15 * mx.random.normal((24, d))         # cookie-cutter cluster opposite
    v = steering_vector(elite, generic)
    align = float(v @ elite_dir)
    print(f"  recovered steering vector ↔ true elite direction: cos = {align:.3f}")
    assert align > 0.9, align
    h = -elite_dir * 2.0                                            # a 'generic' activation to steer
    before = float(h @ elite_dir)
    after = float(inject(h[None], v, alpha=0.4)[0] @ elite_dir)
    print(f"  generic activation projection onto elite: {before:+.2f} → {after:+.2f}  (steered toward elite ✓)")
    assert after > before
    # rung-4 HOOK: wire a mock layer, verify the forward output is steered + removal is clean
    holder = type("H", (), {})(); holder.model = type("H", (), {})()
    holder.model.layers = [lambda x: -elite_dir * mx.ones((1, 1, d))]   # a 'generic' layer output
    remove = apply_steering(holder, 0, v, alpha=0.4)
    hooked = holder.model.layers[0](mx.zeros((1, 1, d)))
    proj = float(hooked[0, 0] @ elite_dir)
    print(f"  HOOK wired into layer → output steered toward elite: proj = {proj:+.2f}")
    assert proj > -1.0
    remove()
    assert not isinstance(holder.model.layers[0], _SteeredLayer)        # cleanly unwired
    print("  design_steering selftest PASS — extracts the elite-art DIRECTION + WIRES a hook that injects it")
    print("  into the residual stream (ActAdd/RepE). Generic prompt → elite, mechanistically. GPU captures real acts.")


if __name__ == "__main__":
    _selftest()
