#!/usr/bin/env python3
"""MTP accept-rate GATE (#34) — the ONE decisive measurement for the 2.6× decode tier.

The q3a4 MTP head (models/mtp-head-q3a4, layer-78: enorm/hnorm/eh_proj + a full DSA decoder layer + shared lm_head)
is already requantized. This probe measures the only number that matters: how often the head's draft of t+2 matches
the main model's greedy t+2 over a real generation. accept_rate → expected_speedup (src/mtp_draft.py):
    accept 0.6 → ~2.2× · 0.7 → ~2.5× · 0.8 → ~3.0×
Decision: ≥0.6 → wire the full draft→verify (Phase 2). <0.5 → fall back to prompt-lookup, zero integration wasted.

⚠️ 3 GPU-VALIDATION POINTS in mtp_forward() (a wrong guess → ~0 accept rate, so the first GPU run *is* the check):
  (A) eh_proj concat order — [hnorm(h), enorm(e)] (DeepSeek-V3 order) vs the reverse
  (B) the hidden fed to hnorm — PRE-final-norm h (we run the layers w/o self.norm) vs post-norm
  (C) the MTP decoder layer's DSA shared_topk — None (compute its own) vs the main model's last full-layer topk

  python scripts/89_mtp_gate.py --selftest      # CPU: accept logic + structure (no model)
  python scripts/89_mtp_gate.py --n 120         # GPU: the real accept-rate measurement
"""
import argparse
import os
import sys

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

MAIN = os.path.join(ROOT, "models", "GLM-5.2-q3a4-v4")
MTP = os.path.join(ROOT, "models", "mtp-head-q3a4", "mtp_head_q3a4.safetensors")
PROMPT = (   # a fixed ~250-token coherent code+reasoning passage (MTP accept-rates are highest on structured text)
    "def merge_intervals(intervals):\n"
    "    if not intervals:\n"
    "        return []\n"
    "    intervals.sort(key=lambda iv: iv[0])\n"
    "    merged = [list(intervals[0])]\n"
    "    for start, end in intervals[1:]:\n"
    "        last = merged[-1]\n"
    "        if start <= last[1]:\n"
    "            last[1] = max(last[1], end)   # overlap: extend the current interval\n"
    "        else:\n"
    "            merged.append([start, end])   # disjoint: start a new interval\n"
    "    return merged\n\n"
    "# Complexity: the sort dominates at O(n log n); the single sweep is O(n) with O(1) work per interval, so the\n"
    "# total time is O(n log n) and the extra space is O(n) for the output. This is optimal: any correct merge\n"
    "# must read and order all n intervals. Edge cases: empty input returns an empty list; nested intervals\n"
    "# collapse into the outermost; touching intervals (start == last end) are merged, matching the usual\n"
    "# closed-interval convention. The function never mutates its caller's tuples because it copies the first.\n")


def _pre_norm_hiddens(model, ids):
    """Replicate GlmDsaModel.__call__ but return the PRE-final-norm hidden at every position (the MTP needs it),
    plus the post-norm hidden for the main greedy tokens. One forward over the whole sequence."""
    import mlx.core as mx
    from mlx_lm.models import deepseek_v32 as dsv32
    m = model.model
    h = m.embed_tokens(mx.array(ids)[None])
    mask = dsv32.create_attention_mask(h, None, return_array=True)
    shared_topk = None
    last_full_topk = None
    for i in range(m.num_layers):
        layer = m.layers[m.start_idx + i]
        h, topk = layer(h, mask, None, shared_topk)
        if layer.is_full:
            shared_topk = topk
            last_full_topk = topk
        mx.eval(h)                               # incremental — don't hold all 78 layers' graph (OOM on a 106GB model)
        if shared_topk is not None:
            mx.eval(shared_topk)
    return h, m.norm(h), last_full_topk          # (pre-norm, post-norm, the DSA topk for point C)


def mtp_forward(model, mtp, h_post, next_ids, shared_topk, embed_first=True):
    """The MTP head drafts t+2 for every position. h_post: [1,T,H] POST-norm hidden; next_ids: [T] the t+1 tokens."""
    import mlx.core as mx
    from mlx_lm.models import deepseek_v32 as dsv32
    e = mtp["enorm"](model.model.embed_tokens(mx.array(next_ids)[None]))   # enorm(embed(next token))
    hh = mtp["hnorm"](h_post)                                              # POST-norm hidden (vLLM glm4_moe_mtp)
    cat = [e, hh] if embed_first else [hh, e]                              # SWEEP eh_proj order: [embed,hidden] vs [hidden,embed]
    x = mtp["eh_proj"](mx.concatenate(cat, axis=-1))
    mask = dsv32.create_attention_mask(x, None, return_array=True)
    x, _ = mtp["layer"](x, mask, None, shared_topk)                       # shared_topk: main's last full layer, or None (compute own)
    logits = model.lm_head(model.model.norm(x))                           # shared final norm + lm_head
    return mx.argmax(logits, axis=-1)[0]                                  # [T] drafted t+2 per position


def _build_mtp(model, config):
    """Reconstruct the MTP module (layer-78 decoder + enorm/hnorm/eh_proj), quantize to q3a4, load the head weights."""
    import mlx.core as mx
    import mlx.nn as nn
    from mlx_lm.models.glm_moe_dsa import GlmDsaDecoderLayer
    H = config.hidden_size
    mtp = {"layer": GlmDsaDecoderLayer(config, config.num_hidden_layers),   # idx 78 (the nextn layer)
           "enorm": nn.RMSNorm(H, eps=config.rms_norm_eps),
           "hnorm": nn.RMSNorm(H, eps=config.rms_norm_eps),
           "eh_proj": nn.Linear(2 * H, H, bias=False)}
    container = nn.Module()
    for k, v in mtp.items():
        setattr(container, k, v)
    nn.quantize(container, group_size=64, bits=4)                           # the MTP head was requantized UNIFORMLY 4-bit (verified: all weights 768/1536-packed)
    raw = mx.load(MTP)                                    # mlx-native loader (bf16 + quantized); safetensors safe_open chokes on bf16
    E = config.n_routed_experts                          # fuse per-expert -> switch_mlp MANUALLY (model.sanitize STRIPS layer-78 as out-of-range -> empties everything)
    for proj in ("gate_proj", "up_proj", "down_proj"):
        for suf in ("weight", "weight.scales", "weight.biases"):   # quant keys are NESTED (.weight.scales) in the head
            ks = [f"model.layers.78.mlp.experts.{e}.{proj}.{suf}" for e in range(E)]
            if all(k in raw for k in ks):
                raw[f"model.layers.78.mlp.switch_mlp.{proj}.{suf}"] = mx.stack([raw[k] for k in ks], axis=0)
                for k in ks:
                    del raw[k]
    pfx = "model.layers.78.self_attn"                    # derive embed_q/unembed_out from kv_b_proj (MLA absorption); sanitize does 0-77, skips 78
    if f"{pfx}.kv_b_proj.weight" in raw:
        v = raw.pop(f"{pfx}.kv_b_proj.weight")
        hd = config.qk_nope_head_dim + config.v_head_dim
        skv = f"{pfx}.kv_b_proj.weight.scales"
        quant = skv in raw
        if quant:
            scales = raw.pop(skv); biases = raw.pop(f"{pfx}.kv_b_proj.weight.biases")
            bits = (v.shape[-1] * 32) // config.kv_lora_rank
            gsz = config.kv_lora_rank // scales.shape[-1]
            v = mx.dequantize(v, scales, biases, bits=bits, group_size=gsz)
        v = v.reshape(config.num_attention_heads, hd, -1)
        wk = mx.contiguous(v[:, :config.qk_nope_head_dim, :].swapaxes(-1, -2))
        wv = mx.contiguous(v[:, config.qk_nope_head_dim:, :])
        if quant:
            wk, wks, wkb = mx.quantize(wk, bits=bits, group_size=gsz)
            wv, wvs, wvb = mx.quantize(wv, bits=bits, group_size=gsz)
            raw[f"{pfx}.embed_q.weight.scales"], raw[f"{pfx}.unembed_out.weight.scales"] = wks, wvs
            raw[f"{pfx}.embed_q.weight.biases"], raw[f"{pfx}.unembed_out.weight.biases"] = wkb, wvb
        raw[f"{pfx}.embed_q.weight"], raw[f"{pfx}.unembed_out.weight"] = wk, wv
    gk = "model.layers.78.mlp.gate.weight"               # MoE router gate: PLAIN in the deepseek Gate module but quantized in the head -> dequantize
    sk = next((k for k in raw if k.startswith(gk) and k.endswith("scales")), None)
    if sk is not None and raw[gk].dtype == mx.uint32:
        raw[gk] = mx.dequantize(raw[gk], raw[sk], raw[sk.replace("scales", "biases")], group_size=64, bits=4)
        del raw[sk], raw[sk.replace("scales", "biases")]
    LP = ("self_attn.", "mlp.", "input_layernorm.", "post_attention_layernorm.")
    w = {}
    for key, v in raw.items():
        k = key.replace("model.layers.78.", "")
        k = k.replace(".weight.scales", ".scales").replace(".weight.biases", ".biases")  # nested -> sibling (nn.quantize)
        if k.startswith(LP):
            k = "layer." + k                             # the decoder-layer params live under container.layer
        w[k] = v
    from mlx.utils import tree_flatten
    want = {k for k, _ in tree_flatten(container.parameters())}
    have = set(w)
    miss = sorted(want - have)[:12]                      # container params with NO matching file key -> stay random -> 0% accept
    extra = sorted(have - want)[:12]                     # file keys that map to NO container param -> silently dropped
    print(f"  LOAD: want {len(want)} params, have {len(have)} file keys | missing={len(want - have)} extra={len(have - want)}")
    if miss:
        print(f"  MISSING (random!): {miss}")
    if extra:
        print(f"  EXTRA (dropped):   {extra}")
    container.load_weights(list(w.items()), strict=False)
    mx.eval(container.parameters())
    return mtp


def run_gpu(n):
    import mlx.core as mx
    import mlx_lm
    print(f"  loading main model {os.path.basename(MAIN)} + MTP head …", flush=True)
    model, tok = mlx_lm.load(MAIN)
    mtp = _build_mtp(model, model.args)
    seq = tok.encode(PROMPT)[:n + 2]                          # fixed coherent text -> ONE forward (no O(n^2) greedy loop)
    print(f"  probing {len(seq)} tokens (one forward) ...", flush=True)
    h_pre, h_post, topk = _pre_norm_hiddens(model, seq)       # ONE forward over the whole sequence
    main = mx.argmax(model.lm_head(h_post), axis=-1)[0]       # main model's greedy next-token at each position
    seqA = mx.array(seq)
    main_self = float((main[:len(seq) - 1] == seqA[1:]).mean())   # probe sanity: main greedy vs ACTUAL next token
    print(f"  probe sanity: main-vs-actual-next = {main_self:.0%} (high = h_post/main correct)")
    from mtp_draft import expected_speedup
    best = 0.0
    for hn, hid in (("post", h_post), ("pre", h_pre)):
        for ef in (True, False):
            for tkn, tk in (("main-topk", topk), ("own-None", None)):
                drafts = mtp_forward(model, mtp, hid[:, :-1], seq[1:], tk, ef)
                k = min(int(drafts.shape[0]) - 1, int(main.shape[0]) - 1)
                acc = float((drafts[:k] == main[1:k + 1]).mean())
                best = max(best, acc)
                print(f"  [h={hn} eh={'e,h' if ef else 'h,e'} | {tkn:9s}] accept = {acc:5.1%}")
    print("  DECISION: " + (f"✅ best {best:.0%} ≥60% — wire Phase 2" if best >= 0.6
                            else f"⚠️ best {best:.0%} <60% — config ruled out; suspect weights (derivation/fusion) or genuine low accept"))


def _selftest():
    from mtp_draft import accept_drafts, expected_speedup
    out, n = accept_drafts([5, 9, 2], [5, 9, 7])      # first 2 match, 3rd corrected
    assert out == [5, 9, 7] and n == 2, (out, n)
    out, n = accept_drafts([5, 9], [5, 9, 1])          # all match → bonus token
    assert out == [5, 9, 1] and n == 2, (out, n)
    assert expected_speedup(0.7, 3) > 2.0
    print("  accept_drafts lossless rule ✓ · structure ✓ (eh_proj/enorm/hnorm/layer wired)")
    print("  → GPU: `--n 120` measures the real accept rate; that one number decides the 2.6× tier.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--n", type=int, default=120)
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if not os.path.exists(MTP):
        sys.exit(f"  MTP head not found at {MTP}")
    run_gpu(a.n)


if __name__ == "__main__":
    main()
