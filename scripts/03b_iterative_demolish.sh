#!/usr/bin/env bash
# Iterative prune + heal — the quality-preserving way to demolish.
#
# One 60% expert cut is brutal. Instead remove experts in STAGES, healing (LoRA)
# and fusing between each, so the model re-balances its surviving experts before
# the next cut. Retains far more quality at the same final size.
#
# Each stage: REAP-prune the (healed) model -> LoRA heal -> fuse -> checkpoint.
# REAP re-profiles saliency on the calibration set each stage, so it always cuts
# the currently-least-useful experts. Eval each checkpoint to find your stop point.
#
# RATIOS = fraction of CURRENT experts to remove per stage (compounds). Each must
# leave a group-valid expert count (multiple of n_group) or 03_prune hard-fails.
# Example below removes ~0.30, 0.30, 0.20 -> cumulative kept 0.7*0.7*0.8 ≈ 0.39
# (≈61% removed) across 3 gentler stages.
set -euo pipefail
cd "$(dirname "$0")/.."

START="${START:-models/GLM-5.2-mxfp4}"
RATIOS=(${RATIOS:-0.35 0.35 0.30})   # ~70% removed total (fits 128GB at 3-bit)
HEAL_ITERS="${HEAL_ITERS:-600}"
HEAL_LAYERS="${HEAL_LAYERS:-16}"
CALIB="${CALIB:-calibration/calib.jsonl}"
export PYTHONPATH="$PWD/src:${PYTHONPATH:-}"

[ -f heal/data/train.jsonl ] || { echo "build heal data first (06b/06)"; exit 1; }

prev="$START"
for i in "${!RATIOS[@]}"; do
  ratio="${RATIOS[$i]}"
  pruned="models/stage$i-pruned"
  healed="models/stage$i-healed"
  echo "================ STAGE $i : remove ${ratio} of remaining experts ================"

  echo ">> [$i] prune $prev -> $pruned"
  MODEL="$prev" OUT="$pruned" RATIO="$ratio" CALIB="$CALIB" bash scripts/03_prune.sh

  echo ">> [$i] heal (LoRA, $HEAL_ITERS iters) on $pruned"
  python3 scripts/06_heal_lora.py --model "$pruned" --skip-data \
    --iters "$HEAL_ITERS" --num-layers "$HEAL_LAYERS"

  echo ">> [$i] fuse adapter -> $healed (so next stage prunes healed weights)"
  python3 -m mlx_lm fuse --model "$pruned" \
    --adapter-path heal/adapters --save-path "$healed"

  echo ">> [$i] checkpoint size:"; du -sh "$healed" || true
  echo ">> [$i] EVAL this checkpoint:  MODEL=$healed bash scripts/05_serve.sh  then"
  echo "        python3 scripts/07_eval.py --label stage$i --vs-flagship"
  echo ">> [$i] (optional) free space:  rm -rf $pruned $prev_tmp"

  prev="$healed"
done

echo "================ DONE ================"
echo ">> Final iteratively-demolished+healed model: $prev"
echo ">> Quantize it:  python3 scripts/04_quantize.py --src $prev --method dwq"
echo ">> Compare stage evals to pick the best quality/size trade-off."
