#!/usr/bin/env python3
"""#34 step 3/4 — quantize the extracted MTP head (models/mtp-head, bf16, 19GB) to MATCH the model's q3a4
scheme: experts (mlp.switch_mlp.{gate,up,down}_proj) → 3-bit, everything else → 4-bit, group_size 64 affine
(verified from models/GLM-5.2-q3a4-v4/config.json). Produces models/mtp-head-q3a4/, ready to attach as layer
78 in glm_moe_dsa.py + drive the draft→verify loop (mtp_draft.py). Uses mx.quantize → GPU; run when free.

  python scripts/74_quantize_mtp.py
"""
import json
import os

import mlx.core as mx

SRC = "models/mtp-head/mtp_head.safetensors"
OUT = "models/mtp-head-q3a4"
GS = 64


def bits_for(name):
    """3-bit for MoE expert matrices (matches the model), 4-bit default for everything else."""
    if "switch_mlp" in name and any(p in name for p in ("down_proj", "gate_proj", "up_proj")):
        return 3
    return 4


def main():
    if not os.path.exists(SRC):
        print(f"  {SRC} missing — run 72_extract_mtp.py --extract first"); return
    os.makedirs(OUT, exist_ok=True)
    w = mx.load(SRC)
    out, qcfg, nq = {}, {"group_size": GS, "bits": 4, "mode": "affine"}, 0
    for name, t in w.items():
        # quantize weight MATRICES only (≥2D, last dim divisible by group_size); keep norms/biases/1D as bf16
        if name.endswith(".weight") and t.ndim >= 2 and "norm" not in name and t.shape[-1] % GS == 0:
            b = bits_for(name)
            wq, scales, biases = mx.quantize(t, group_size=GS, bits=b)
            out[name], out[name + ".scales"], out[name + ".biases"] = wq, scales, biases
            if b != 4:
                qcfg[name[: -len(".weight")]] = {"group_size": GS, "bits": b, "mode": "affine"}
            nq += 1
        else:
            out[name] = t
    mx.eval(list(out.values()))
    mx.save_safetensors(os.path.join(OUT, "mtp_head_q3a4.safetensors"), out)
    json.dump(qcfg, open(os.path.join(OUT, "quantization.json"), "w"), indent=2)
    print(f"  quantized {nq} MTP-head matrices (experts 3-bit / rest 4-bit, gs={GS}) -> {OUT}")
    print("  next: attach as layer 78 in glm_moe_dsa.py + wire mtp_draft.accept_drafts into the decode loop")


if __name__ == "__main__":
    main()
