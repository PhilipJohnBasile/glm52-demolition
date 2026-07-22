#!/bin/bash
# Factory chain (#73/#74/#76/#77) — heal each domain specialty as a SWAPPABLE adapter on v4, sequentially,
# waiting for the GPU between each. Autonomous ~12h: 6 souls here + gamedev already running = 7 total.
# Each is v4 + adapters-<spec>; the model-factory swaps the adapter to change the model's specialty.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # repo root = scripts/..
cd "$REPO_ROOT"
LOG=heal/factory_chain.log
echo "$(date) :: factory-chain START — queue: legacy security fullstack science factory perfumery" >> "$LOG"
for spec in legacy security fullstack science factory perfumery; do
  while pgrep -f "mlx_lm lora" >/dev/null 2>&1; do sleep 60; done          # wait for the GPU to free
  n=$(wc -l < "heal/_q_$spec/train.jsonl" 2>/dev/null)
  echo "$(date) :: healing $spec ($n train)" >> "$LOG"
  GLM_STREAM_EVAL=0 .venv/bin/python scripts/06_heal_lora.py \
    --model models/GLM-5.2-q3a4-v4 --data "heal/_q_$spec" --skip-data --no-mask-prompt \
    --adapter-path "heal/adapters-$spec" --iters 800 --num-layers 16 --max-seq-length 2048 --batch-size 1 \
    >> "heal/${spec}.heal.log" 2>&1
  echo "$(date) :: $spec DONE -> heal/adapters-$spec" >> "$LOG"
done
touch heal/FACTORY_DONE
echo "$(date) :: FACTORY-CHAIN COMPLETE — 7 swappable souls" >> "$LOG"
