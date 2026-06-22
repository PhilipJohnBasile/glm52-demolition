# Wiring the demolished GLM-5.2 into an agent harness

Point your harness at the **think-proxy** (controllable thinking) and register
**search_code** (code RAG). Full local agentic coding loop.

## Serving stack (3 processes)
```bash
# 1) the model (OpenAI endpoint :8080)  — add DRAFT_MODEL=... for speculative
MODEL=models/GLM-5.2-demolished-mxmix bash scripts/05_serve.sh

# 2) controllable-thinking proxy (:8081) — point your harness HERE, not :8080
python scripts/08_think_proxy.py --port 8081 --upstream http://localhost:8080

# 3) code RAG — pick ONE integration:
#    a) MCP (Claude Code / Cline / Zed):   scripts/16_rag_mcp.py  (see below)
#    b) HTTP tool (custom executor):       python scripts/11_rag_server.py --port 8090
```

## Harness configs

### Claude Code / Cline / Zed (MCP) — `.mcp.json`
```json
{
  "mcpServers": {
    "code-rag": {
      "command": "python",
      "args": ["scripts/16_rag_mcp.py", "--index", "rag/index"]
    }
  }
}
```
Then set the model base URL to `http://localhost:8081/v1` (the think-proxy).

### opencode — `opencode.json`
```json
{
  "provider": {
    "local-glm": {
      "npm": "@ai-sdk/openai-compatible",
      "options": { "baseURL": "http://localhost:8081/v1" },
      "models": { "GLM-5.2-demolished": {} }
    }
  }
}
```

### Aider
```bash
aider --openai-api-base http://localhost:8081/v1 \
      --openai-api-key local --model GLM-5.2-demolished
```
(Aider has no custom-tool slot; use the HTTP RAG as a manual `/run` helper, or
prefer an MCP-capable harness for automatic search_code.)

## Why this layout
- `:8081` proxy gives per-step thinking control (on for reasoning, off for tool
  steps) + budget — see `scripts/08_think_proxy.py`.
- `search_code` lets the agent retrieve the few relevant files instead of whole
  repos: smarter, faster, less context. The agent decides when to call it.
- Re-index when your code changes:
  `python scripts/10_rag_index.py --repos ~/code/yourproj --out rag/index`

---
## The agentic engine (2026-06-17) — supersedes the 3-process notes above
The model now drives a 47-tool ReAct agent: `python scripts/57_tool_agent.py --repo PATH --apply
--task "..." --test "cargo test"`. Tools: read/write/run/run_tests/search_code(callsieve)/grep/
**verify(any domain: code+lint, sql, math, design)**/repl/sympy/arxiv/web_search/see(VLM)/browse/
screenshot/gen_image. Verified decoding: `scripts/41`. Multi-agent + adversarial: `51`. The
verifier mesh (`src/verifiers.py verify_domain`) is the correctness spine.
- **Dev tools (2026-06-17)**: `git` (status/diff/commit/branch/PR), `code_intel` (LSP def/refs/hover),
  `profile` (cProfile), `pg` (Postgres/sqlite) — the agent navigates + ships like a senior engineer.
- **Integrity layer (2026-06-17)**: test-tamper guard (no reward-hacking the tests), fabrication-proof
  `done` (real verifier proof required, not a claim), scope enforcement, slopsquat guard (deps must
  exist on the real registry). The verifier is the incorruptible source of truth.
