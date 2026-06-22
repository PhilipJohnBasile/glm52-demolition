# Speed — the MEASURED reality (M5 Max 128 GB)

**Root cause (confirmed): decode is memory-bandwidth bound** — every token reloads expert weights from the
~106 GB model. The honest conclusion that follows was *measured*, not guessed (2026-06-18):

> **Every single-stream speedup lever has been benchmarked, and every one is dead on this MoE.**
> ~11–14 tok/s is the hard memory floor. You cannot speculate your way under it.

| Lever | Hoped | **MEASURED** | Why it fails |
|---|---|---|---|
| MTP self-speculative | ~2.6× | **0% accept** (`89_mtp_gate.py`) | the native head is UN-pruned (256 experts) vs our pruned 77 → its MoE/router don't match → garbage drafts |
| External draft model | 1.5–2.5× | **0.32× (proxy)** | the batched *verify* forward reloads ~all 77 experts; also draft+main ≈126/128 GB + Metal-unstable |
| Prompt-lookup (no model) | 2–4× | **0.32×** (`src/prompt_lookup.py`) | lossless ✓ but the same MoE verify-wall — 8.4 tok/forward, but each forward loads ~all experts |
| dsa-block-size / index_topk | ~1.3× | **flat 1.00–1.03×** (`90_dsa_sweep.py`) | attention is NOT the bottleneck; the MoE expert-load dominates |
| Reduce active experts 8→6 | ~25% | **quality-dead** (`22_speed_tune.py`) | the router was trained for top-8 of the pruned 77; can't drop post-prune without a full re-prune+heal |

### The physics
A MoE decode step is bound by loading the active experts' weights. Any *multi-token* speculative forward
(MTP, draft-model, or n-gram) loads the **union** of experts for those tokens (~all 77) → costs ~K× a single
step → the per-forward token gain is exactly cancelled. So **no speculative method beats single-token decode here.**
Proven 4 independent ways, $0 spent (vs the $4–15K an EAGLE retrain would have cost to discover the same thing).

### What ACTUALLY delivers speed (and is already shipped)
1. **Fused MoE dequant-matmul Metal kernel** (#33) — this *is* the 11–14 tok/s; it's the real win.
2. **Throughput via batching — MEASURED 2.6× at B=8** (`scripts/91_batch_scaling.py`): total decode
   **15.8 → 27.1 → 34.6 → 41.1 tok/s** at B = 1 / 2 / 4 / 8. On a memory-bound MoE, *parallel sequences* are
   the lever — one expert-load serves the whole batch (per-seq drops, total climbs). This is where "faster"
   actually lives (best-of-N, proof-search, multi-agent, the flywheel), and `mlx_lm.server` batches concurrent
   requests **natively** (`is_batchable`, no draft model — that's us), so the win is available at the serve (#71).
   **Serve-verified: 1.74× at B=6** on the live `mlx_lm.server` (concurrent vs sequential, `scripts/92_serve_batch_test.py`)
   — already shipping; just fire concurrent requests. The ONLY measured speedup on this model that beats 1×.

### Free, orthogonal wins (prefill / TTFT — not decode tok/s)
- **Prompt/prefix KV cache** (`05_serve.sh --prompt-cache-size`) — agentic loops resend the same system+tools;
  cache the prefix → big *time-to-first-token* cut. Real, but it doesn't move the decode tok/s number.
- **M5 Neural Accelerators / current MLX** — free generation + prefill gains from keeping `mlx` current.
- **`08_think_proxy.py`** — skip the thinking trace on trivial structural steps → fewer tokens, not faster/token.

### The ONLY path to a single-stream speedup (not recommended)
Train a **fresh EAGLE-3 head** on the demolished model's own outputs (architecture-agnostic, ~1B dense layer):
~$4–15K cloud H100 or ~weeks of local M5 data-gen. And even then it's **uncertain** — EAGLE on a fast MoE
baseline measured ~1.03× in the literature (same verify-wall). See `#69`. Bank the batching instead.

### Bottom line
Single-stream is **memory-capped at ~11–14 tok/s and that's the floor**. The speed pillar is the fused kernel
(#33) + throughput batching (#35/#48), both built. Don't fight physics; batch for throughput.

*(Receipts: `89_mtp_gate.py` → 0%, `src/prompt_lookup.py --bench` → 0.32×, `90_dsa_sweep.py` → flat. Full log
in OVERNIGHT_LOG.md under the 2026-06-18 speed entries.)*
