#!/bin/bash
# Autonomous overnight driver: heal-wait -> upload -> serve -> benchmarks -> report.
# Launched via Bash run_in_background; progress streamed to OVERNIGHT_LOG.md.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # repo root = scripts/..
cd "$REPO_ROOT"
LOG=OVERNIGHT_LOG.md
REPO=philipjohnbasile/GLM-5.2-Demolition-q3a4-MLX
say() { echo "[$(date '+%m-%d %H:%M')] $*" >> "$LOG"; }

say "================ OVERNIGHT RUN START ================"

# ---- STAGE A: soul heal -> upload ----
say "STAGE A: waiting for soul heal SFT (06_heal_lora) to finish..."
while pgrep -f 06_heal_lora >/dev/null 2>&1; do sleep 30; done
if [ -f heal/adapters-soul/adapters.safetensors ]; then
  say "STAGE A DONE: $(grep -E 'Iter [0-9]+: (Train|Val) loss' logs/soul_sft.log | tail -1)"
  if .venv/bin/hf upload "$REPO" heal/adapters-soul adapters-soul >> "$LOG" 2>&1; then
    say "STAGE A: adapters-soul UPLOADED to HF (ok)"
  else
    say "STAGE A: HF upload FAILED (adapter safe on disk; continuing)"
  fi
  ADAPTER="--adapter-path heal/adapters-soul"
else
  say "STAGE A: NO adapter produced -- see logs/soul_sft.log. Benchmarking BASE model."
  ADAPTER=""
fi

# ---- STAGE B: serve + benchmarks ----
say "STAGE B: launching serve ${ADAPTER:-(base)}..."
pkill -f mlx_lm.server 2>/dev/null; pkill -f serve_stable 2>/dev/null; sleep 3
GLM_STREAM_EVAL=0 nohup .venv/bin/python scripts/serve_stable.py --model models/GLM-5.2-q3a4-v4 $ADAPTER --port 8080 > logs/serve_bench.log 2>&1 &
for i in $(seq 1 90); do curl -s localhost:8080/v1/models >/dev/null 2>&1 && break; sleep 5; done
if ! curl -s localhost:8080/v1/models >/dev/null 2>&1; then
  say "STAGE B: serve FAILED to start (see logs/serve_bench.log) -- skipping benchmarks"
  say "================ OVERNIGHT RUN COMPLETE (heal only) ================"
  exit 0
fi
say "STAGE B: serve UP (ok)"

say "STAGE B1: HumanEval-164 starting (~1.5h)..."
if .venv/bin/python scripts/58_bench.py --n 164 >> "$LOG" 2>&1; then say "STAGE B1 DONE (HumanEval ok)"; else say "STAGE B1 errored (continuing)"; fi
say "STAGE B2: GSM8K/STEM starting (~3h)..."
if .venv/bin/python scripts/59_stem_diag.py >> "$LOG" 2>&1; then say "STAGE B2 DONE (GSM8K ok)"; else say "STAGE B2 errored (continuing)"; fi
say "STAGE B3: study-loop starting (capped 2h)..."
if timeout 7200 .venv/bin/python scripts/87_lean_study.py >> "$LOG" 2>&1; then say "STAGE B3 DONE (study-loop ok)"; else say "STAGE B3 errored/skipped"; fi

pkill -f serve_stable 2>/dev/null; pkill -f mlx_lm.server 2>/dev/null
say "================ OVERNIGHT RUN COMPLETE ================"
