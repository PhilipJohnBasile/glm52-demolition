# Agent Gateway — run our model in any coding agent (the Ollama-style backend)

Start once:  `python scripts/serve_stable.py`  (model on :8080)  +  `python scripts/agent_gateway.py` (:8090)
The gateway adds: sane sampling defaults (no 3-bit collapse) · OpenAI function-calling · Anthropic /v1/messages.

MODEL = `philipjohnbasile/GLM-5.2-Demolition-q3a4-MLX`

## CLI
- **aider:**   `OPENAI_API_BASE=http://localhost:8090/v1 OPENAI_API_KEY=x aider --model openai/$MODEL`
- **Codex CLI:** `OPENAI_BASE_URL=http://localhost:8090/v1 OPENAI_API_KEY=x codex --model $MODEL`

## VSCode
- **Cline:** Provider = "OpenAI Compatible" · Base URL `http://localhost:8090/v1` · Model `$MODEL`
- **Continue.dev:** config → provider "openai", `apiBase: http://localhost:8090/v1`, `model: $MODEL`

## Claude Code on our model (the "another instance of Claude" path)
`ANTHROPIC_BASE_URL=http://localhost:8090 ANTHROPIC_API_KEY=x claude`
(gateway translates Anthropic /v1/messages <-> our serve, incl. tool_use)

NOTE: function-calling is prompt-injected + parsed (the 3-bit model isn't natively tool-trained) — works,
but a tool-trained heal (#114 + an agentic-tool SFT) will make it crisp. callsieve + best-of-N remain the
reliable fix path under any harness.
