#!/usr/bin/env python3
"""Saliency-weighted DYNAMIC quantization — our answer to Unsloth Dynamic 2.0.

Unsloth Dynamic 2.0 gives each layer a custom bit-width by an *undisclosed* importance metric, calibrated on
>1.5M conversational tokens, judged by KL-divergence vs the BF16 model. We can match-or-beat it with a metric we
ALREADY compute and that is principled + disclosed: the **REAP router-weighted saliency** (router_weight ×
activation_norm) used to decide pruning. So the experts we KEEP get bits in proportion to how much they matter —
high-saliency experts get more bits, low-saliency fewer, averaging to a target. Feeds scripts/04_quantize (per-
expert `--plan`). Evaluate the result by KL-divergence (see kl_div note). CPU.

  python src/dynamic_bits.py        # selftest
"""
import numpy as np


def allocate_bits(saliency, target_avg=3.0, levels=(2, 3, 4)):
    """Per-expert bit-width by saliency. Greedy water-fill from the top: raise the highest-saliency experts as
    high as the average-bit budget allows, so bits are non-increasing in saliency and mean ≈ target_avg."""
    s = np.asarray(saliency, dtype=float)
    n = len(s)
    levels = sorted(int(x) for x in levels)
    bits = np.full(n, levels[0], dtype=int)
    target_total = round(target_avg * n)
    total = int(bits.sum())
    for e in np.argsort(-s):                       # highest saliency first
        for nxt in levels[1:]:                     # raise this expert as far as the remaining budget permits
            step = nxt - bits[e]
            if step > 0 and total + step <= target_total:
                total += step
                bits[e] = nxt
    return bits


def layer_plan(layer_saliency, target_avg=3.0, levels=(2, 3, 4)):
    """Per-LAYER bit plan for `04_quantize --plan` → {layer_index: bits}. Fused MoE = one tensor per layer = one
    bit-width, so per-LAYER is the feasible dynamic granularity (same as Unsloth's "every layer"). Aggregate the
    per-expert REAP saliency to per-layer (mean over that layer's kept experts) first, then allocate.
    Usage: json.dump(layer_plan(per_layer_saliency, 3.0), open('plan.json','w')); python 04_quantize --plan plan.json"""
    bits = allocate_bits(np.asarray(layer_saliency, dtype=float), target_avg, levels)
    return {int(i): int(b) for i, b in enumerate(bits)}


def summary(saliency, bits):
    s = np.asarray(saliency, float)
    from collections import Counter
    dist = dict(sorted(Counter(bits.tolist()).items()))
    # correlation between saliency rank and bits (should be strongly positive)
    corr = float(np.corrcoef(s, bits)[0, 1]) if len(set(bits)) > 1 else 1.0
    return {"avg_bits": round(float(bits.mean()), 3), "dist": dist, "saliency_corr": round(corr, 3)}


def _selftest():
    rng = np.random.default_rng(0)
    sal = np.sort(rng.gamma(2.0, 1.0, size=77))[::-1]      # 77 experts, realistic skewed saliency
    for tgt in (3.0, 2.5, 3.5):
        bits = allocate_bits(sal, target_avg=tgt, levels=(2, 3, 4))
        info = summary(sal, bits)
        # 1) average hits target (±0.1); 2) bits non-increasing in saliency order; 3) positive saliency↔bits corr
        assert abs(info["avg_bits"] - tgt) <= 0.1, (tgt, info)
        order_bits = bits[np.argsort(-sal)]
        assert all(order_bits[i] >= order_bits[i + 1] for i in range(len(order_bits) - 1)), "not saliency-monotone"
        assert info["saliency_corr"] > 0.5, info
        print(f"  target {tgt}: avg={info['avg_bits']} dist={info['dist']} corr={info['saliency_corr']}")
    plan = layer_plan(rng.gamma(2.0, 1.0, size=92), target_avg=3.0)        # 92 MoE layers → per-layer plan JSON
    assert len(plan) == 92 and abs(float(np.mean(list(plan.values()))) - 3.0) <= 0.1, plan
    print(f"  layer_plan: {len(plan)} layers, avg {float(np.mean(list(plan.values()))):.2f} bits → feeds 04_quantize --plan ✓")
    print("  dynamic_bits selftest PASS — saliency-weighted bits, mean=target, monotone in importance "
          "(REAP saliency = the principled metric Unsloth keeps undisclosed). Eval the result by KL-div vs BF16.")


if __name__ == "__main__":
    _selftest()
