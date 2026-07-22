#!/bin/bash
# Sound-chain — the final autonomous stage. Waits for the compounding loop to close (post_chain's LOOP_CLOSED),
# then runs the sound-flywheel (model writes sound code → verify('sound') keeps the good audio → fills the
# gold), then heals the SOUND SOUL on it. The full night: factory_chain (7 souls) → post_chain (repair soul)
# → sound_chain (sound soul). Fully unattended; the GPU never idles.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # repo root = scripts/..
cd "$REPO_ROOT"
LOG=heal/sound_chain.log
echo "$(date) :: sound-chain up — waiting for LOOP_CLOSED" >> "$LOG"
while [ ! -f heal/LOOP_CLOSED ]; do sleep 120; done
while pgrep -f "mlx_lm lora" >/dev/null 2>&1; do sleep 60; done            # GPU free?
echo "$(date) :: filling sound gold via the flywheel (gen→run→verify→keep)" >> "$LOG"
GLM_STREAM_EVAL=0 .venv/bin/python scripts/sound_flywheel.py --target 200 --adapter heal/adapters-soul2 >> "$LOG" 2>&1
n=$(wc -l < heal/gold_sound/sound.jsonl 2>/dev/null)
echo "$(date) :: sound gold = $n examples; assembling + healing the sound soul" >> "$LOG"
mkdir -p heal/_q_sound
cp heal/gold_sound/sound.jsonl heal/_q_sound/train.jsonl
while pgrep -f "mlx_lm lora" >/dev/null 2>&1; do sleep 60; done
GLM_STREAM_EVAL=0 .venv/bin/python scripts/06_heal_lora.py \
  --model models/GLM-5.2-q3a4-v4 --data heal/_q_sound --skip-data --no-mask-prompt \
  --adapter-path heal/adapters-sound --iters 400 --num-layers 16 --max-seq-length 2048 --batch-size 1 \
  >> heal/sound.heal.log 2>&1
touch heal/SOUND_DONE
echo "$(date) :: SOUND SOUL healed -> heal/adapters-sound. The model can score + SFX now." >> "$LOG"
