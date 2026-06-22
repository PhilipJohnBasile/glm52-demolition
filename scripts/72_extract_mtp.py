#!/usr/bin/env python3
"""#34 — extract the MTP head (layer 78) from the zai-org/GLM-5.2 ORIGINAL, which ships it; our prune
dropped it. Layer 78 = the nextn head: enorm/hnorm/eh_proj + shared_head + a full transformer block
(self_attn + MoE). Quantize + attach to the pruned model → self-speculative decoding (~1.3-2x, per
mlx-lm PR #990 / MTPLX, which self-draft from the model's own MTP head — no 2nd model). GPU-free numpy.

  python scripts/72_extract_mtp.py            # inventory layer 78 (zero memory, safe anytime)
  python scripts/72_extract_mtp.py --extract  # write models/mtp-head/ (needs ~12 GB free RAM; run when GPU frees)
"""
import argparse
import glob
import json
import os

_snaps = sorted(glob.glob(os.path.expanduser(
    "~/.cache/huggingface/hub/models--zai-org--GLM-5.2/snapshots/*")))
ORIG = _snaps[0] if _snaps else None
OUT = "models/mtp-head"


def layer78_tensors():
    idx = json.load(open(glob.glob(ORIG + "/*.index.json")[0]))["weight_map"]
    return {k: idx[k] for k in idx if k.startswith("model.layers.78.")}


def download_layer78():
    """Fetch the shards holding layer 78 from zai-org/GLM-5.2 (BF16) into the HF cache so --extract can read
    them. HF downloads whole files, so these shards also carry other layers (~tens of GB, not a clean 10 GB) —
    but it's the supported path. Run when disk+bandwidth allow (NOT while the flywheel is using memory)."""
    from huggingface_hub import hf_hub_download
    idx = json.load(open(glob.glob(ORIG + "/*.index.json")[0]))["weight_map"]
    shards = sorted({idx[k] for k in idx if k.startswith("model.layers.78.")})
    print(f"  downloading {len(shards)} shard(s) holding layer 78 from zai-org/GLM-5.2 ...")
    for s in shards:
        hf_hub_download("zai-org/GLM-5.2", s)
        print(f"    ✓ {s}")
    return shards


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true", help="fetch the layer-78 shards from HF first (~tens of GB)")
    ap.add_argument("--extract", action="store_true", help="write the tensors to models/mtp-head/ (needs ~12GB RAM)")
    args = ap.parse_args()
    if not ORIG:
        print("  original zai-org/GLM-5.2 not found in HF cache"); return
    t = layer78_tensors()
    cats = {}
    for k in t:
        sub = k.split("model.layers.78.")[1].split(".")[0]
        cats[sub] = cats.get(sub, 0) + 1
    print(f"  MTP layer 78: {len(t)} tensors across {len(set(t.values()))} shard file(s)")
    for c, n in sorted(cats.items()):
        print(f"    {c:24s} {n} tensor(s)")
    if args.download:
        download_layer78()
    if not args.extract:
        print("  (inventory only — run --extract when the GPU/memory frees to write models/mtp-head/)")
        return
    import mlx.core as mx                              # MLX is bf16-native (numpy is not → TypeError)
    byfile = {}
    for k, f in t.items():
        byfile.setdefault(f, []).append(k)
    os.makedirs(OUT, exist_ok=True)
    tensors = {}
    for fname, keys in byfile.items():
        shard = mx.load(os.path.join(ORIG, fname))      # whole shard lazy (~5GB); pick layer-78 keys, free rest
        for k in keys:
            if k in shard:
                tensors[k] = shard[k]
        mx.eval(list(tensors.values()))                 # materialize the kept tensors
        del shard
    mx.save_safetensors(os.path.join(OUT, "mtp_head.safetensors"), tensors)
    print(f"  extracted {len(tensors)} MTP-layer-78 tensors -> {OUT}/mtp_head.safetensors")
    print("  next: stream-quantize to q3a4 + attach as layer 78 in glm_moe_dsa.py, add the draft→verify loop")


if __name__ == "__main__":
    main()
