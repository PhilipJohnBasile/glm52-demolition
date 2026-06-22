#!/usr/bin/env bash
# Download the source model for demolition.
#
# We prune the ALREADY-4-bit mxfp4 repo (~395 GB) rather than the 1.51 TB BF16,
# because the BF16 will not fit your 1.6 TB free disk alongside intermediates.
# Pruning 4-bit weights is lossier than pruning bf16 then quantizing, but it is
# the only option that fits local disk. (If you later get >2 TB free, switch
# SRC to the bf16 repo for a cleaner prune->quantize.)
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="${SRC:-mlx-community/GLM-5.2-mxfp4}"
DEST="${DEST:-models/GLM-5.2-mxfp4}"

echo ">> Free disk:"; df -h . | tail -1
echo ">> Downloading $SRC -> $DEST (~395 GB, this takes a while)"

# hub >=1.x: use `hf` (huggingface-cli is deprecated); Xet replaces hf_transfer.
command -v hf >/dev/null 2>&1 || uv pip install -q "huggingface_hub[cli]"
export HF_XET_HIGH_PERFORMANCE=1
# optional: export HF_TOKEN=... for higher rate limits / faster downloads

hf download "$SRC" \
  --local-dir "$DEST" \
  --exclude "*.gguf" --exclude "original/*"

echo ">> Done. Verify config model_type:"
python3 - "$DEST" <<'PY'
import json, sys
c = json.load(open(f"{sys.argv[1]}/config.json"))
print("  model_type:", c.get("model_type"))
print("  n_routed_experts:", c.get("n_routed_experts"))
print("  num_experts_per_tok:", c.get("num_experts_per_tok"))
print("  n_group / topk_group:", c.get("n_group"), "/", c.get("topk_group"))
print("  num_hidden_layers:", c.get("num_hidden_layers"))
PY
