#!/usr/bin/env bash
# One-command setup for the demolished GLM-5.2.
# Two things this guarantees:
#   (1) the model can be LOADED   -> patch mlx_lm/LM Studio's glm_moe_dsa stub
#   (2) the model can USE CallSieve -> install the binary + register the MCP server
# The model is TRAINED to reach for CallSieve; this installs the tool it reaches for.
#
#   bash dist/setup.sh [target-repo]     # default target-repo = current dir
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="${CALLSIEVE_BIN:-$HOME/.local/bin/callsieve}"
REPO="${1:-$PWD}"

echo ">> 1/4 CallSieve binary (the zero-token retrieval tool)"
if command -v callsieve >/dev/null 2>&1; then
  BIN="$(command -v callsieve)"; echo "   on PATH: $BIN ($("$BIN" --version 2>/dev/null))"
elif [ -x "$HOME/git/callsieve/target/release/callsieve" ]; then
  mkdir -p "$(dirname "$BIN")"
  cp "$HOME/git/callsieve/target/release/callsieve" "$BIN"; chmod +x "$BIN"
  echo "   installed -> $BIN ($("$BIN" --version 2>/dev/null))"
else
  echo "   [need it] build:  (cd ~/git/callsieve && cargo build --release)"
  echo "            or:     cargo install callsieve"
  exit 1
fi

echo ">> 2/4 glm_moe_dsa patch (so mlx_lm + LM Studio can LOAD the model)"
python3 "$HERE/install_glm_dsa_patch.py" || echo "   (skipped: no mlx_lm found yet)"

echo ">> 3/4 register CallSieve as the MCP retrieval server for $REPO"
cat > "$REPO/.mcp.json" <<JSON
{
  "mcpServers": {
    "callsieve": { "type": "stdio", "command": "$BIN", "args": ["mcp"], "env": {} }
  }
}
JSON
echo "   wrote $REPO/.mcp.json"

echo ">> 4/4 index $REPO (first retrieval is then instant)"
"$BIN" index "$REPO" >/dev/null 2>&1 && echo "   indexed" || echo "   (index builds on first query)"

cat <<'NOTE'
DONE.
  - The model will call callsieve_context / callsieve_symbol / callsieve_tests
    instead of grepping. If CallSieve is ever missing, it falls back to grep
    (recommend the system prompt include that fallback line; see SETUP.md).
  - LM Studio users: fully quit + reopen so the patched engine reloads.
NOTE
