#!/usr/bin/env bash
# Expert-prune GLM-5.2 with REAP, using our group-aware adapter.
#
# COMPRESSION_RATIO = fraction of routed experts to REMOVE. To land under your
# memory budget you need a large ratio; pick one whose surviving expert count is
# a multiple of n_group (the adapter will hard-fail otherwise — by design).
#
# Example: if n_routed_experts=256 and n_group=8, valid keep counts are
# multiples of 8 -> 96 kept (ratio 0.625), 80 kept (0.6875), 64 kept (0.75)...
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${MODEL:-models/GLM-5.2-mxfp4}"
RATIO="${RATIO:-0.625}"           # remove 62.5% of routed experts
CALIB="${CALIB:-calibration/calib.jsonl}"
OUT="${OUT:-models/GLM-5.2-pruned}"
MAX_SAMPLES="${MAX_SAMPLES:-256}"
MAX_SEQ="${MAX_SEQ:-8192}"   # REAP recipe uses 16384; 8192 is a 128GB-safe compromise

REAP_DIR="reap-mlx"
export PYTHONPATH="$PWD/src:${PYTHONPATH:-}"

echo ">> Pruning $MODEL  (remove ${RATIO} of routed experts) -> $OUT"
echo ">> Registering GLM-5.2 adapter into reap-mlx..."

# Run reap's entrypoint with our adapter registered first (same process).
cd "$REAP_DIR"
uv run python - "$MODEL" "$CALIB" "$RATIO" "$OUT" "$MAX_SAMPLES" "$MAX_SEQ" <<'PY'
import sys, runpy
sys.path.insert(0, "../src")
import glm52_reap_adapter as gad
gad.register()
print("  adapter registered:", gad.Glm52MoeModelAdapter.adapter_name)

model, calib, ratio, out, msamp, mseq = sys.argv[1:7]
sys.argv = [
    "reap.entrypoint",
    "--model-name", f"../{model}",
    "--dataset-name", f"../{calib}",   # local jsonl path
    "--prune-method", "reap",
    "--compression-ratio", ratio,
    "--max-samples", msamp,
    "--max-seq-length", mseq,
    "--output-dir", f"../{out}",
    "--verbose",
]
runpy.run_module("reap.entrypoint", run_name="__main__")
PY

echo ">> Pruned model at $OUT"
