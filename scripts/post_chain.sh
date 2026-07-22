#!/bin/bash
# Auto-close the compounding loop (#16) — runs AFTER the factory chain. Waits for FACTORY_DONE, then preps
# repair-SFT data from the FULL flywheel output, heals soul-v4 on it (adapters-repair), and runs the
# repair-eval gate. Unattended: mine -> heal -> measure, the loop closes by itself. Launch in bg now; it
# sleeps until the 7 souls finish (~10h), then does the tail.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # repo root = scripts/..
cd "$REPO_ROOT"
LOG=heal/post_chain.log
echo "$(date) :: post-chain up — waiting for FACTORY_DONE" >> "$LOG"
while [ ! -f heal/FACTORY_DONE ]; do sleep 120; done
echo "$(date) :: souls done — prepping repair-data from the flywheel" >> "$LOG"
.venv/bin/python src/hardneg_to_sft.py --in heal/hardnegs_rich.jsonl --out heal/_q_repair/train.jsonl >> "$LOG" 2>&1
.venv/bin/python -c "
import json
L=[l for l in open('heal/_q_repair/train.jsonl').read().splitlines() if l.strip()]
open('heal/_q_repair/eval.jsonl','w').write(chr(10).join(L[-40:]))
open('heal/_q_repair/train.jsonl','w').write(chr(10).join(L[:-40]))
print(f'  split: {len(L)-40} train / 40 eval')
" >> "$LOG" 2>&1
while pgrep -f "mlx_lm lora" >/dev/null 2>&1; do sleep 60; done          # GPU free?
echo "$(date) :: healing the repair soul (closing the loop)" >> "$LOG"
GLM_STREAM_EVAL=0 .venv/bin/python scripts/06_heal_lora.py \
  --model models/GLM-5.2-q3a4-v4 --data heal/_q_repair --skip-data --no-mask-prompt \
  --adapter-path heal/adapters-repair --iters 600 --num-layers 16 --max-seq-length 2048 --batch-size 1 \
  >> heal/repair.heal.log 2>&1
echo "$(date) :: repair soul healed — running the repair-eval gate" >> "$LOG"
GLM_STREAM_EVAL=0 .venv/bin/python scripts/repair_eval.py --adapter heal/adapters-repair \
  --eval heal/_q_repair/eval.jsonl >> "$LOG" 2>&1
touch heal/LOOP_CLOSED
echo "$(date) :: LOOP CLOSED — mine -> heal -> measure, fully autonomous" >> "$LOG"
