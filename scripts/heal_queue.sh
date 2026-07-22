#!/usr/bin/env bash
# Autonomous factory heal-queue: heal the swappable "brains" one at a time
# (GPU-serial, ~1.7h each), ship each on completion. Idempotent — state is
# derived from disk (which adapters-<name>/adapters.safetensors exist), so it is
# safe to re-run on every wake. Each adapter is self-contained (Pattern A):
# the proven soul_gold2 base + that module's specialty gold.
set -u
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # repo root = scripts/..
cd "$REPO_ROOT" || exit 1
REPO=philipjohnbasile/GLM-5.2-Demolition-q3a4-MLX
ORDER=(soul-v3 fullstack gamedev legacy)

golds_for() {
  case "$1" in
    soul-v3)   echo "soul_gold2 gold_science gold_perfumery gold_cyber gold_pentest gold_factory" ;;
    fullstack) echo "soul_gold2 gold_fullstack" ;;
    gamedev)   echo "soul_gold2 gold_gamedev" ;;
    legacy)    echo "soul_gold2 gold_legacy" ;;
  esac
}

# 1) A heal is in progress -> wait (GPU is serial).
if pgrep -f 06_heal_lora >/dev/null; then
  echo "[queue] heal in progress — waiting"
  exit 0
fi

# 2) Ship any completed-but-unshipped adapter.
for n in "${ORDER[@]}"; do
  ad="heal/adapters-$n"
  if [ -f "$ad/adapters.safetensors" ] && [ ! -f "$ad/.shipped" ]; then
    echo "[queue] shipping $n ..."
    if hf upload "$REPO" "$ad" "adapters-$n" 2>&1 | tail -1; then
      touch "$ad/.shipped"
      echo "[queue] $n shipped"
    fi
  fi
done

# 3) Launch the next un-healed brain.
for n in "${ORDER[@]}"; do
  ad="heal/adapters-$n"
  if [ ! -f "$ad/adapters.safetensors" ]; then
    echo "[queue] assembling + launching: $n"
    .venv/bin/python scripts/assemble_heal.py "heal/_q_$n" $(golds_for "$n") || exit 1
    GLM_STREAM_EVAL=0 nohup .venv/bin/python scripts/06_heal_lora.py \
      --model models/GLM-5.2-q3a4-v4 --data "heal/_q_$n" --skip-data --no-mask-prompt \
      --adapter-path "$ad" --iters 700 --max-seq-length 2048 --batch-size 1 \
      > "logs/heal_$n.log" 2>&1 &
    echo "[queue] $n heal launched (pid $!)"
    exit 0
  fi
done

echo "[queue] ALL DONE — every brain healed + shipped"
