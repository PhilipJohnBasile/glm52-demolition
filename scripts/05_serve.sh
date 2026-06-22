#!/usr/bin/env bash
# Serve the demolished model FAST. Tuned for agentic coding on M5 Max:
#   - prompt/prefix cache -> huge TTFT cut when agents resend system+tools
#   - bigger prefill      -> faster first token on long inputs
#   - parallel prompts    -> concurrent agent steps/tools
#   - optional draft model-> speculative decoding (1.5-2.5x), set DRAFT_MODEL
# NOTE: KV-cache quantization (--kv-bits) exists in `mlx_lm generate`/cache_prompt
# but NOT in the server CLI in 0.31.3, so it is intentionally not set here.
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true   # so mlx_lm is importable
export GLM_STREAM_EVAL="${GLM_STREAM_EVAL:-0}"   # model fits -> no per-layer eval (faster)

MODEL="${MODEL:-models/GLM-5.2-q3a4-v2}"
PORT="${PORT:-8080}"
ADAPTER="${ADAPTER:-heal/adapters}"     # set ADAPTER= to disable
PREFILL="${PREFILL:-4096}"              # bigger prefill step = faster TTFT
# --prompt-cache-size / --prompt-concurrency crash GLM-5.2's MLA/DSA cache
# (cache.state: 'NoneType' has no 'shape') until the DSA cache implements
# state/from_state. OPT-IN only — empty by default so serving works out of the box.
PROMPT_CACHE="${PROMPT_CACHE:-}"         # set e.g. 8 only after the DSA cache-state fix
CONCURRENCY="${CONCURRENCY:-}"           # set e.g. 2 only after the fix
DRAFT_MODEL="${DRAFT_MODEL:-}"           # e.g. a small GLM w/ SAME tokenizer
NUM_DRAFT="${NUM_DRAFT:-4}"

echo ">> On-disk size:"; du -sh "$MODEL" || true
echo ">> Serving $MODEL on http://localhost:$PORT/v1"

args=(--model "$MODEL" --port "$PORT" --prefill-step-size "$PREFILL")
[ -n "$PROMPT_CACHE" ] && args+=(--prompt-cache-size "$PROMPT_CACHE") || true
[ -n "$CONCURRENCY" ] && args+=(--prompt-concurrency "$CONCURRENCY") || true
[ -n "$ADAPTER" ] && [ -d "$ADAPTER" ] && args+=(--adapter-path "$ADAPTER") && \
  echo "   + LoRA adapter: $ADAPTER"
if [ -n "$DRAFT_MODEL" ]; then
  args+=(--draft-model "$DRAFT_MODEL" --num-draft-tokens "$NUM_DRAFT")
  echo "   + speculative decoding via $DRAFT_MODEL (x$NUM_DRAFT)"
else
  echo "   (set DRAFT_MODEL=<small GLM, same tokenizer> for 1.5-2.5x speedup)"
fi

echo ">> Put scripts/08_think_proxy.py in front (:8081) for controllable thinking."
echo ">> Agent harness base_url -> http://localhost:$PORT/v1 (or :8081 via proxy)"
exec python3 -m mlx_lm.server "${args[@]}"
