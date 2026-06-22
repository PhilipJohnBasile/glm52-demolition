# Run this as your local agentic coder

**The pitch:** not the highest SWE-bench — the **most reliable**. The local agentic coder that *can't break*:
**zero malformed tool-calls** (grammar-enforced, structurally impossible), **compiler-steered every line**,
**fabrication-proof `done`** (re-runs the real tests — can't fake a pass), and elite across the whole stack
(design · math · security · science), not just code. Reliability is the moat raw capability can't buy.

## Serve it (OpenAI-compatible, on your Mac)
```bash
# raise the GPU ceiling once (or long agentic runs OOM):
sudo sysctl iogpu.wired_limit_mb=122000
# serve base + the core soul (OpenAI-compatible on :8080):
GLM_STREAM_EVAL=0 python scripts/serve_stable.py --model models/GLM-5.2-q3a4-v4 \
    --adapter-path heal/adapters-soul2 --port 8080   # serve_stable = memory-guarded; long agentic runs won't OOM/kernel-panic
# optional: concise-thinking proxy (caps reasoning tokens -> faster, cleaner tool turns):
python scripts/08_think_proxy.py --port 8081 --upstream http://localhost:8080
```

## Point your agent at it
Anything that speaks **OpenAI-compatible** drops in against `http://localhost:8080/v1` (or `:8081` for the
think-proxy), any model name:

| Agent | Setup |
|---|---|
| **Cline** (VS Code) | Provider: *OpenAI Compatible* · Base URL `http://localhost:8080/v1` · any model id |
| **Aider** | `aider --openai-api-base http://localhost:8080/v1 --openai-api-key x --model glm-demolition` |
| **OpenCode** | add an OpenAI-compatible provider pointing at `:8080/v1` |
| **Cursor** | Settings → Models → override OpenAI Base URL to `:8080/v1` |
| **Claude Code** | needs an OpenAI→Anthropic shim (or `rapid-mlx`'s `ANTHROPIC_BASE_URL` trick) — Claude Code speaks the Anthropic API, not OpenAI |

**Recommended settings:** `temperature 0.6`, `top_p 0.95` for coding; `enable_thinking` on for hard problems,
off (or the think-proxy budget) for fast tool turns.

## Why it doesn't break (the reliability stack)
- **Grammar-constrained tool-JSON** — invalid tokens get zero probability at each step, so a malformed call is
  *structurally impossible* (vs the field's best: "fewer malformed"). Speaks the 2026 strict-schema + MCP conventions.
- **Verified / compiler-steered decoding** — a line that adds a type error is backtracked as it's written.
- **Fabrication-proof `done`** — the agent re-runs the *original* tests before claiming success; it can't hallucinate a pass.
- **Integrity layer** — test-tamper guard, 16-provider secret-scan, scope enforcement, slopsquat guard.
- **51-tool ReAct agent** — trajectory compaction + stall detection for long-horizon runs; the verifier mesh checks every output against its real tool.

## Beyond code — every chip, every modality
The agent isn't GPU-only. It spreads work across **all six M5 Max compute blocks** so the GPU stays free for
tokens: the **ANE** perceives (OCR · segmentation · pose · object-detection · NER · audio-classify · TTS ·
embed · rerank · route), the **18 CPU cores** verify (the mesh, `verify_many`, 9 langs) + run tabular ML, the
**Media Engine** decodes/encodes video, **AMX** does the matrix math. An **Any-to-Any omni-router**
(`src/omni.py`) sends any input — text · image · audio · video · table — to its optimal block; ASR is
**Whisper on MLX**.

And it's a **factory**: one 99 GB base + hot-swappable ~100 MB LoRA souls (code · design · gamedev · legacy ·
security · fullstack · science · data · perfumery) — swap the adapter, swap the specialty.

## Honest limits (and what's queued to fix them)
- **~11–14 tok/s decode** — the memory trade for a local 743B-class model. *Queued:* NVFP4 + M5 Neural Accelerators
  (~2× decode on M5), throughput batching for concurrent requests (2.6× at B=8 today).
- **Long single generations can degenerate at 3-bit** (Computation Collapse). *Queued:* saliency-dynamic quant
  (#59 — early/late experts at 4-bit) + a serve-layer auto-recovery that re-structures broken tool-output.
- **Needs a 128 GB Mac** — premium tier for now; a 64 GB sibling is deferred (depth before breadth).

The trade we made on purpose: less raw benchmark, in exchange for **reliability + breadth + fully local + verify-everything** — the things that actually decide whether an agent finishes the job.
