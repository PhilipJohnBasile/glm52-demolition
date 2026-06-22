#!/usr/bin/env python3
"""#34 MTP self-speculative — deep-MLX, built in de-risk order. STEP 1 foundation ✓ (hidden state + weights
load). STEP 2 (--build): build the MTP module (a glm_moe_dsa decoder layer + enorm/hnorm/eh_proj/shared_head),
quantize to q3a4, LOAD the weights — verify every tensor binds. STEP 3 (later): the draft forward
[h'=eh_proj(cat(enorm(embed(t)),hnorm(h))); h''=layer(h'); logits=lm_head(shared_head.norm(h''))] + the
accept/reject loop (mtp_draft.py, tested). GPU, ~3min/run.

  python scripts/75_mtp_spec.py --foundation   # step 1
  python scripts/75_mtp_spec.py --build         # step 2
"""
import argparse
import json
import os
import sys

import mlx.core as mx
import mlx.nn as nn
from mlx.utils import tree_flatten

HERE = os.path.dirname(__file__)
MODEL = os.path.join(HERE, "..", "models", "GLM-5.2-q3a4-v4")
MTP_DIR = os.path.join(HERE, "..", "models", "mtp-head-q3a4")
MTP_Q = os.path.join(MTP_DIR, "mtp_head_q3a4.safetensors")


def foundation():
    os.environ["GLM_STREAM_EVAL"] = "0"
    from mlx_lm import load
    print("  loading model (~3min)...", flush=True)
    model, tok = load(MODEL)
    h = model.model(mx.array([tok.encode("The capital of France is")]))
    mx.eval(h)
    print(f"  hidden state {h.shape} {h.dtype} ✓ | MTP weights {len(mx.load(MTP_Q))} tensors ✓")


def build():
    os.environ["GLM_STREAM_EVAL"] = "0"
    from mlx_lm import load
    print("  loading model (~3min)...", flush=True)
    model, tok = load(MODEL)
    cfg = model.args
    layer_cls = type(model.model.layers[0])          # GlmDsaDecoderLayer
    print(f"  layer class: {layer_cls.__name__}")

    class MTPHead(layer_cls):                          # decoder block + MTP projections (keys match layer.78.*)
        def __init__(self, config):
            super().__init__(config, 78)
            d = config.hidden_size
            self.enorm = nn.RMSNorm(d, eps=config.rms_norm_eps)
            self.hnorm = nn.RMSNorm(d, eps=config.rms_norm_eps)
            self.eh_proj = nn.Linear(2 * d, d, bias=False)
            self.shared_head = type("SH", (nn.Module,), {})()
            self.shared_head.norm = nn.RMSNorm(d, eps=config.rms_norm_eps)

    mtp = MTPHead(cfg)
    # quantize to match q3a4 (experts 3-bit, rest 4-bit) using the saved per-module config
    qcfg = json.load(open(os.path.join(MTP_DIR, "quantization.json")))

    def bits_for(path):
        full = "model.layers.78." + path
        return qcfg.get(full, {}).get("bits", 4)

    # load saved weights FIRST; a module was quantized iff it has a `.scales` companion (skips MoEGate/router)
    raw = mx.load(MTP_Q)
    qpaths = {k[: -len(".scales")].replace("model.layers.78.", "") for k in raw if k.endswith(".scales")}
    nn.quantize(mtp, group_size=64, bits=4,
                class_predicate=lambda p, m: (p in qpaths) and {"group_size": 64, "bits": bits_for(p)})
    weights = {k.replace("model.layers.78.", ""): v for k, v in raw.items()}
    params = dict(tree_flatten(mtp.parameters()))
    missing = [k for k in params if k not in weights]
    extra = [k for k in weights if k not in params]
    print(f"  MTP module params: {len(params)} | saved: {len(weights)} | missing: {len(missing)} | extra: {len(extra)}")
    for k in missing[:4]:
        print(f"    missing: {k}")
    for k in extra[:4]:
        print(f"    extra:   {k}")
    if not missing and not extra:
        mtp.load_weights(list(weights.items()))
        mx.eval(mtp.parameters())
        print("  STEP-2 OK — MTP module built + quantized + ALL weights loaded ✓ (next: the draft forward)")
    else:
        print("  STEP-2 key-mismatch — adjust module structure to match saved keys (diagnostics above)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--foundation", action="store_true")
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    foundation() if a.foundation else build() if a.build else print("  --foundation | --build")


if __name__ == "__main__":
    main()
