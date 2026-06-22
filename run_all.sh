#!/usr/bin/env bash
# One-command STREAMING pipeline (the one that actually works on 128GB).
# Replaces the old reap-mlx flow: we stream the >RAM model layer-by-layer.
# Resumable — skips stages whose output already exists.
#
#   bash run_all.sh            # interactive (confirms before the heavy steps)
#   YES=1 bash run_all.sh      # unattended
# Knobs: N=256 SEQ=1024 RATIO=0.70 BITS=3 HEAL_ITERS=1500 HEAL_LAYERS=16
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || true
export PATH="$HOME/.local/bin:/usr/local/go/bin:$PATH"
export PYTHONPATH="$PWD/src:${PYTHONPATH:-}"
export GLM_STREAM_EVAL=0        # the model fits after prune/quant; eval-stream only for >RAM

SRC=models/GLM-5.2-mxfp4
N="${N:-256}"; SEQ="${SEQ:-1024}"; RATIO="${RATIO:-0.70}"; BITS="${BITS:-3}"
HEAL_ITERS="${HEAL_ITERS:-1500}"; HEAL_LAYERS="${HEAL_LAYERS:-16}"; YES="${YES:-0}"
SAL=models/saliency.npz; PRUNED=models/GLM-5.2-pruned; Q3=models/GLM-5.2-q3
RC=models/GLM-5.2-q3-rc
step(){ echo; echo "========== $* =========="; }
confirm(){ [ "$YES" = 1 ] && return 0; read -r -p "$* [y/N] " a||a=""; [ "$a" = y ]||[ "$a" = Y ]; }
have(){ [ -e "$1" ]; }

step "0/8 preflight"; python3 scripts/00_preflight.py
[ -f "$SRC/config.json" ] || { echo "download $SRC first (scripts/01_download.sh)"; exit 1; }

step "1/8 stream-calibrate (true REAP, ~10GB working set)"
have "$SAL" && echo "  $SAL exists, skip" || \
  python3 scripts/23_stream_calibrate.py --data heal/mine/verified.jsonl \
    --n "$N" --seq "$SEQ" --batch 32 --out "$SAL"

step "2/8 apply prune (stream, slice kept experts)"
have "$PRUNED/config.json" && echo "  exists, skip" || { \
  confirm "Prune now?" && python3 scripts/24_apply_prune.py --model "$SRC" \
    --saliency "$SAL" --ratio "$RATIO" --out "$PRUNED"; }

step "3/8 requantize (stream, ${BITS}-bit)"
have "$Q3/config.json" && echo "  exists, skip" || \
  python3 scripts/24b_stream_requantize.py --src "$PRUNED" --bits "$BITS" \
    --group-size 64 --out "$Q3"
echo "  size:"; du -sh "$Q3" || true

step "4/8 router-KD (recalibrate router after the cut)"
have "$RC/config.json" && echo "  exists, skip" || { \
  confirm "Router-KD now?" && python3 scripts/21_router_kd.py --model "$Q3" \
    --data heal/mine/verified.jsonl --out "$RC" || cp -r "$Q3" "$RC"; }

step "5/8 build balanced heal data"
have heal/data/train.jsonl && echo "  exists, skip" || python3 scripts/27_build_heal_data.py

step "6/8 heal (LoRA SFT, ${HEAL_LAYERS} layers)"
have heal/adapters/adapters.safetensors && echo "  exists, skip" || { \
  confirm "Heal now? (~1-2h)" && python3 scripts/06_heal_lora.py --model "$RC" \
    --skip-data --num-layers "$HEAL_LAYERS" --iters "$HEAL_ITERS" --learning-rate 2e-5; }

step "7/8 eval"
echo "  serve then eval (separate terminal):"
echo "    MODEL=$RC ADAPTER=heal/adapters bash scripts/05_serve.sh"
echo "    python3 scripts/08_think_proxy.py --port 8081 &"
echo "    ANTHROPIC_API_KEY=... python3 scripts/07_eval.py --label final --vs-fable"
echo "    python3 scripts/18_agentic_eval.py --base-url http://localhost:8081/v1"

step "8/8 serve (verification-wrapped)"
echo "  best-of-N:  python3 scripts/26_bestofn.py --mode code|design --base-url http://localhost:8081/v1 --task ..."
echo "DONE. Healed model: $RC + heal/adapters"
