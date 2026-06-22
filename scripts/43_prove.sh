#!/usr/bin/env bash
# PROVE IT — the full validation, run the moment the healed model is served. This
# is the "where do we actually stand vs Fable" button, and the live demo of the
# new idea (verified decoding). Everything upstream has been built + unit-validated;
# this turns "built" into "proven" with real numbers.
#
#   # terminal 1 — serve the healed model (+ LoRA adapter):
#   MODEL=models/GLM-5.2-q3a4-v2 ADAPTER=heal/adapters bash scripts/05_serve.sh
#   # terminal 2 — controllable-thinking proxy:
#   python3 scripts/08_think_proxy.py --port 8081 &
#   # then, with a key for the head-to-head:
#   ANTHROPIC_API_KEY=... bash scripts/43_prove.sh
set -uo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"
BASE="${BASE_URL:-http://localhost:8081/v1}"      # via think-proxy
DIRECT="${DIRECT_URL:-http://localhost:8080/v1}"  # raw model (for /completions)

echo "== 0. endpoint check =="
curl -sf "$BASE/models" >/dev/null 2>&1 || curl -sf "$DIRECT/models" >/dev/null 2>&1 \
  || { echo "  model not served — start scripts/05_serve.sh first"; exit 1; }
echo "  served ✓"

echo; echo "== 1. CODE vs Fable — exec-checked, per-language =="
python3 scripts/07_eval.py --base-url "$BASE" --label proof --vs-fable || true

echo; echo "== 2. DESIGN vs Fable — render + measure (WCAG/type-scale/OKLCH/framework-tells) =="
python3 scripts/29_design_vs_fable.py --base-url "$BASE" || true

echo; echo "== 3. VERIFIED DECODING live — the new idea, real tsc/tsgo steering the model =="
python3 scripts/41_verified_decode.py --lang ts --base-url "$DIRECT" \
  --task "Write a typed debounce<T extends (...a:any[])=>void>(fn:T, ms:number) in TS" || true

echo; echo "== 4. BEST-OF-N verification — the frontier-beater (run the tests) =="
python3 scripts/26_bestofn.py --mode code --base-url "$BASE" \
  --task "Write rust dedup_sorted(v:Vec<i32>)->Vec<i32> (sorted, deduped)" \
  --check compile_rust \
  --harness 'fn main(){assert_eq!(dedup_sorted(vec![3,1,2,1,3]),vec![1,2,3]);println!("OK");}' || true

echo; echo "== DONE =="
echo "  This is where we stand vs Fable in the niche, with verified decoding +"
echo "  best-of-N live. Losses here feed 32_hard_negative_mining -> the next heal."
echo "  Then v3: GRPO/RLVR (39) with these verifiers as the reward."
