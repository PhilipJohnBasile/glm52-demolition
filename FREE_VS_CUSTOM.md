# Free (mlx-lm) vs Custom — stop rebuilding what ships (audit 2026-06-21)

## ✅ FREE in mlx-lm 0.31.3 — USE THE FLAG/FEATURE, don't rebuild
| Capability | Our task | How to get it FREE |
|---|---|---|
| Speculative decode | #10/#115 | `--draft-model <tiny-mlx> --num-draft-tokens N` (server flag) — try Qwen2.5-0.5B draft |
| Prompt cache (LRU+nearest+save/load) | #25/#85 | `--prompt-cache-size --prompt-cache-bytes` flags; cache_prompt.py save_prompt_cache |
| Batching / concurrency | #48/#71 | `--decode-concurrency --prompt-concurrency --prefill-step-size` flags |
| Sampling defaults | (gateway hack) | `--temp 0.6 --top-p 0.95 --min-p` server flags → can replace gateway default-injection |
| Quantized KV (INT8 NA path) | #117 | QuantizedKVCache EXISTS; only gap = expose `--kv-bits` (1 small server patch) |
| Rotating/long-context KV | #86 | RotatingKVCache in generate.py |
| LoRA trainer | #114/06_heal | already wraps `mlx_lm.lora` ✓ (not reinventing) |
| logits_processors hook | #32-45 | server passes them; our ConstrainedSampler plugs in ✓ |

## 🔒 GENUINELY OURS — no free equivalent, real value (KEEP)
- **callsieve** — retrieval/localization (nothing comparable).
- **best-of-N + verifier loop** (bestofn_fix) — the agentic fix orchestration.
- **Constrained tool-JSON / structured output (#45)** — mlx-lm has **NO** response_format/json_schema/grammar (verified). This is genuinely ours = the native-tool reliability path (XGrammar-level guarantee isn't free).
- **glm_moe_dsa** — our DSA sparse-attention (upstreamed #49).
- **agent_gateway** — Anthropic /v1/messages translation + GLM tool-parse (mlx-lm ships ONLY a deepseek_v32 parser; **no GLM parser, no Anthropic endpoint**).
- **GLM tool parser** — not shipped → add one to mlx-lm chat_templates/ (small, like deepseek_v32.py) OR keep gateway parse.

## ACTION (free wins, next serve restart)
1. Add free flags to serve_stable launch: `--draft-model` (spec, measure accept), `--prompt-cache-size/bytes`, `--decode-concurrency`, `--temp 0.6 --top-p 0.95` (defaults).
2. Small patch: expose `--kv-bits 8 --kv-group-size 64` in server.py → INT8 KV on the M5 NA (the #117 win).
3. Keep #45 constrained tool-JSON (not free) as the native-tool reliability layer.
4. Optionally add a GLM tool-parser to mlx-lm (upstreamable) for true mlx-native tool_calls.

## 🔭 FULL-STACK MLX-ecosystem audit (2026-06-21) — every build vs a free equivalent
Installed free packages: **mlx_lm 0.31.3, mlx_vlm 0.6.3, mlx_whisper 0.4.3, mlx_audio, mflux, mlx_embeddings 0.1.0**.

### ⬆️ ADOPT — free MLX equivalent we should switch to / lean on
| Our build | Free MLX equivalent | Action |
|---|---|---|
| #62-67/#105 custom bench harnesses | **mlx_lm.evaluate + lm_eval** (standard: mmlu/gsm8k/arc/hellaswag) | ADOPT — credible STANDARD numbers, drop custom |
| #60 KL/quant eval | **mlx_lm.perplexity / losses.py** | ADOPT for #60 |
| #59 saliency-dynamic quant | **mlx_lm.convert class_predicate** (mixed-bit) + **dwq.py** | use convert predicate; investigate DWQ |
| #114 quant-accuracy recovery | **mlx_lm.dwq** (Distilled Weight Quant) | INVESTIGATE — if teacher-feasible (layer-wise?), a free recovery path alongside rejection-sampling |
| #73 model factory (fuse adapters) | **mlx_lm.fuse** | ADOPT — fuse LoRA→standalone model |
| #2/#114 LoRA train | **mlx_lm.lora** | already wrapping ✓ |
| #43 vision/VLM | **mlx_vlm 0.6.3** | ADOPT — free VLM inference |
| #99 ASR | **mlx_whisper** | already using ✓ |
| #92/#100 TTS / audio-gen | **mlx_audio** | ADOPT |
| #42/#95/#101 image gen | **mflux** (FLUX) | ADOPT |
| #78/#89 embeddings (GPU) | **mlx_embeddings 0.1.0** | option; but our ANE/CoreML offload (#78) frees the GPU → KEEP ANE, mlx_embeddings = GPU fallback |
| #51 GGUF | **mlx_lm.gguf / convert** | ADOPT |
| serve flags / KV / cache / spec | mlx_lm.server flags + QuantizedKVCache + draft-model (see top of doc) | #120 in flight |

### 🔒 KEEP — genuinely ours, NO MLX equivalent (verified)
callsieve (#6) · best-of-N+verifier orchestration (#113) · **constrained decoding #32-45** (mlx-lm has NO grammar/response_format) · GRPO/RLVR (#18, no mlx trainer) · prompt-lookup (#70) · FIM primitives (#35) · **glm_moe_dsa** (#49, OUR upstreamed contribution) · the **agent_gateway** (no GLM parser / Anthropic endpoint in mlx-lm) · 57-agent (#57) · soul/heal-data pipelines + verifier-mesh (#26) + Lean prover (#27-31) · REAP prune (#1, Cerebras not mlx) · **ANE/CoreML lanes (#78-99)** — ANE ≠ MLX (MLX=GPU); the ANE offload is the WHOLE POINT (frees GPU), so not redundant.

### TOP UPGRADES to grab (ranked): 1) mlx_lm.evaluate+lm_eval (standard benches, credibility) · 2) DWQ for #114 (free quant-recovery — investigate teacher need) · 3) mlx_lm.fuse for #73 factory · 4) mflux/mlx_audio/mlx_vlm for media lanes · 5) serve free-flags+kv-bits (#120, in flight).
