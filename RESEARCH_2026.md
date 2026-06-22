# RESEARCH 2026 — Speed + Accuracy Mission (verified, sourced, re-ranked)

Deep multi-source sweep (arXiv · HuggingFace · GitHub · Reddit) + a **verification pass** on every finding
("is it real, is there something better?"). Date: 2026-06-21. Living doc — update as levers are measured.
Companion to HEADTOHEAD_RESEARCH.md (chronology) and BACKLOG.md (the queue). Sources linked inline.

---

## ✅ VERIFICATION VERDICT (what changed after the second pass)

| Lever | Finding | Verified? | Anything better? |
|---|---|---|---|
| #114 recover accuracy | Recover-LoRA / QAD (FP-teacher KL distill) | ⚠️ recipe real BUT **FP teacher infeasible** for us (pruned BF16 ≈500GB ≫128GB) | ✅ **YES — our pivot is the SOTA path**: verifier-gated **rejection-sampling FT** ("distillation predominantly relies on rejection sampling — verified positives only"); Apple self-distillation (Apr-2026) confirms teacher-free works |
| #113 best-of-N | verifier-gated best-of-N, provably > verifier-free (√H gap) | ✅ confirmed | ➖ GenRM (generative verifier) = 6.4× fewer samples — **but only where there's NO executable test**; we have `cargo test` (perfect exec verifier) → best-of-N+test is already optimal for CODE. GenRM is the lever for our NON-code lanes (design/prose) |
| #113 localization | function-level repair > line (45.6 vs 43.6%), lower variance | ✅ confirmed | line-first then function-fallback (instance-dependent) |
| #117 KV compress | TurboQuant/PolarQuant 6× @3-bit, MLX-native | ✅ **confirmed best**: beats KIVI (2.6×), SnapKV/PyramidKV (info-loss) | watch OSCAR / EpiCache (the 2026 race); **int4-KV outruns fp16 on Apple Silicon** = free speedup |
| #110 MoE-Sieve | routing-guided saliency (REAP) > weight-norm | ✅ confirmed (REAP, DR-LoRA, ConMoE) | routing×activation-norm; our 49% (weight-norm) is a floor |
| MLX M5 | INT8 = NA fast path (2× over fp16); MLX≥0.30 = NA support | ✅ confirmed (Apple) | prefer INT8; TurboQuant k_bits=8 hits the NA path |
| #115 EAGLE/spec | marginal on MoE (~1.05×, 34% accept) | ✅ confirmed (mlx-lm #890) — DEPRIORITIZE | decode win isn't here for MoE |

**Bottom line:** every finding held up; the only *correction* was #114 (FP teacher infeasible → verifier-gated
rejection-sampling FT, which the literature says is the dominant approach anyway). One genuine *upgrade* found
(GenRM for non-code lanes). One free Apple-Silicon win (int4 KV > fp16).

---

## 🥇 #114 — Recover accuracy WITHOUT an FP teacher (the top lever)

**Constraint:** literal Recover-LoRA ([2606.04238](https://arxiv.org/abs/2606.04238)) / QAD ([NVIDIA 2601.20088](https://arxiv.org/abs/2601.20088))
distill from a full-precision teacher's logits. Our pruned GLM-5.2 at BF16 ≈ 500GB — does NOT fit 128GB; a 4-bit
teacher (~132GB) doesn't either. **No full teacher is runnable locally.**

**Pivot (SOTA-confirmed, teacher-free):** verifier-gated **rejection-sampling fine-tuning** — generate synthetic
bugs → fix with best-of-N → keep ONLY `cargo test`-verified-correct fixes → SFT the model to one-shot them.
- Confirmed: "current distillation predominantly relies on rejection sampling — leveraging only positive examples
  whose final answers are VERIFIED" (search result). Apple's self-distillation (Apr-2026, sample-own-outputs-then-FT)
  confirms teacher-free recovery works. [AuPair](https://arxiv.org/pdf/2502.18487) (golden example pairs for code repair) +
  [RL-Synthesizes-Reusable-Solvers](https://arxiv.org/html/2605.18374) ("outperforms best-of-N + self-repair, far less
  diminishing returns") = the "amortize search into the policy" family our callsieve+best-of-N already embodies.
- The "teacher" = best-of-N + verifier (a provably-better policy than single-shot, the √H result) distilled into the
  student. Recovers accuracy **and speed** (one-shots next time → fewer candidates).
- Optional logit refinement: BitDistiller-style fwd+rev KL self-distillation on the same data.
- **STATUS: BUILT + RUNNING** — `scripts/recover_datagen.py` (verified fixes → `recover_data.jsonl`); SFT via
  `06_heal_lora.py` on next GPU-exclusive window (heal max-seq ≤2048 per the DSA limit). Crash-safe: serve generates,
  cargo verifies, then stop-serve → train (never two big models).

## 🥈 #113 — best-of-N is optimal FOR CODE; GenRM is the lever for non-code

- Verifier-gated best-of-N is provably > verifier-free ([2502.12118](https://arxiv.org/pdf/2502.12118), √H gap). For CODE we
  have `cargo test` = a perfect execution verifier → nothing beats it on sample-correctness.
- [Generative Verifiers / GenRM-CoT](https://arxiv.org/abs/2408.15240): match Best-of-32 with **6.4× fewer samples**,
  5%→45.3% algorithmic, 73%→93.4% GSM8K — **but that's for tasks WITHOUT an executable test**. → adopt GenRM for our
  DESIGN / PROSE / non-test lanes; keep execution-verification for code.
- Localization: function-level (45.6%) > line (43.6%) > file ([2604.00167](https://arxiv.org/html/2604.00167v1)); instance-dependent.
  → `bestofn_fix`: line-first (cracks operator-flips in 1 cand), function-level fallback for multi-line.
- Efficiency: [VG-Search](https://arxiv.org/abs/2505.11730) +3.6% at −52% FLOPs; [Surprisal-Guided Selection](https://arxiv.org/pdf/2602.07670)
  (compute-optimal TTC for execution-grounded code). Strengthen verifier with model-generated extra tests
  ([2602.04254](https://arxiv.org/pdf/2602.04254)).
- **MEASURED (ours): 3/4 real bugs, subtle operator-flips 2/2 in 1 candidate.**

## 🥉 #110 — routing-guided saliency
Upgrade the sieve metric from ‖A‖·‖B‖ (weight-norm, gave 49% reduction) to **router-gate × activation-norm**
([REAP](https://github.com/CerebrasResearch/reap)), routing-freq + grad-rank ([DR-LoRA](https://arxiv.org/html/2601.04823v5)),
or unlabeled-calib routing stats ([ConMoE](https://arxiv.org/html/2605.29350)). [MoE-Sieve](https://arxiv.org/html/2603.24044)
= routing-guided LoRA, 70-73% param cut ≈ full LoRA. Needs a calibration forward pass (GPU). Should keep more quality
at the same size, or safely reach 500MB.

## ⚡ #117 — TurboQuant KV (best-in-class) + the Apple-Silicon free win
- TurboQuant/PolarQuant ([2504.19874](https://arxiv.org/html/2504.19874v1)) = best 2026 KV compressor: 6× @3-bit, no
  calibration, near info-theoretic limit; at 2.5-bit LongBench 49.44 / Needle 0.997 (holds). Beats KIVI (2.6×),
  SnapKV/PyramidKV (token-pruning = info loss).
- **[int4 KV outruns fp16 on Apple Silicon](https://arxiv.org/html/2605.05699v1)** — low-bit KV is a *free* speedup on
  M-series (less bandwidth). Pairs with M5-NA INT8 fast-path. MLX ports: rachittshah/mlx-turboquant, VeloxQuant-MLX.
- Caveat: not in stock mlx-lm as of Apr-2026 → community port. Watch [OSCAR / EpiCache](https://www.marktechpost.com/2026/06/18/the-kv-cache-compression-race-turboquant-vs-oscar-vs-epicache/).

## 🍎 MLX M5 Max enhancements
MLX v0.30 = M5 Neural-Accelerator support (macOS≥26.2; we're on 27). NA = per-GPU-core matmul units (Tensor-Core-like,
unified-memory-coupled). **INT8 = 2× over fp16** on the NA; 4× TTFT prefill + 3.8× FLUX vs M4, automatic. → prefer INT8
paths; the prefill win is free on current MLX. ([Apple](https://machinelearning.apple.com/research/exploring-llms-mlx-m5))

## 📉 #115 / #69 — EAGLE/spec decode: DEPRIORITIZED (evidence)
[mlx-lm #890](https://github.com/ml-explore/mlx-lm/discussions/890): EAGLE-3 on MLX = 34% accept → 1.34 tok/step → ~1.05×
on the hard/MoE case (dense gets 3.75×, ALU-bound). Tree-attention blocked by single-offset-RoPE KVCache. Matches our
prior "MTP measured-dead on MoE". The decode win is not here.

## 🎯 Local rivals to beat (#111)
[Qwen3-Coder-30B-A3B-MLX](https://dev.to/danishashko/the-best-llms-for-agentic-coding-in-2026-real-world-not-just-benchmarks-96n)
= the June-2026 local pick (~30-35 tok/s M4 Pro, Q4_K_M ~17GB); also DeepSeek-V4, Kimi-K2.6. MLX ~15-25% > GGUF. Pull
via `lms get --mlx` for the same-scaffold model-only axis (NEVER GGUF).

---

## EVIDENCE-RANKED ROADMAP
1. **#114** verifier-gated rejection-sampling FT (teacher-free, SOTA-confirmed) — biggest accuracy, building now.
2. **#113** function-level fallback + GenRM for non-code lanes — cheap, measured 3/4.
3. **#110** routing-guided saliency — better metric, CPU+calib.
4. **#117** TurboQuant int8/int4 KV on M5-NA — free Apple-Silicon speedup, community MLX port.
5. ~~#115 EAGLE~~ — marginal on MoE, parked.

## 🔧 NATIVE TOOL-CALLING + AGENT-BACKEND research (2026-06-21 deep dive)

### GLM-5.2 is BUILT for this (validates our model choice)
GLM-5.2 follows the standard OpenAI two-step tool_calls pattern AND is **built on an Anthropic-compatible API framework — it natively parses Anthropic tools + tool_choice, no translation layer needed** (z.ai docs). Terminal-Bench 2.1 = **81.0** (GLM-5.1 was 62). So our demolished model inherits a native-agentic, Anthropic-compatible format — exactly the Claude Code path. Restore template (DONE) + heal (quant degraded it) + constrain (below).

### mlx-lm tool parsing is PER-MODEL (the catch)
mlx-lm parses tool calls via model-specific parsers auto-detected from chat-template patterns (qwen3_coder.py etc.). KNOWN GAPS: Qwen3.5/3.6 + Gemma 4 native tool calls AREN'T parsed → tool_calls field stays empty (mlx-lm issues #1293, #1096). → Likely **mlx-lm has NO GLM parser** → even with our restored template, mlx-lm renders tools but may not parse GLM's `<tool_call>` output → our **gateway parse-fallback is doing the work** (fine). To be truly mlx-native: add a GLM tool-parser to mlx-lm (upstreamable, like #49) OR keep the gateway parse.
- **Rapid-MLX** (github raullenchai/Rapid-MLX): drop-in OpenAI MLX server, "100% tool calling, 17 tool parsers, Claude Code/Cursor/Aider". ❌ **EXCLUDED — its compatibility badge lists M1|M2|M3|M4, NO M5** (we're M5 Max). Don't adopt. Our own serve_stable is already M5-native (mlx≥0.30 NA, macOS 27). Borrow its IDEAS (17 parsers, reasoning-separation) but not the dep.

### ⭐ THE reliability lever: CONSTRAINED DECODING for tool calls (we already have it — #45)
XGrammar-2 (arXiv 2601.04426): grammar-constrained decoding = **100% schema-valid tool-call arguments**, eliminates malformed calls. CRUCIAL: **"the added value INCREASES as the model gets smaller" — constrained Llama-3.2-3B OUTPERFORMS unconstrained Llama-3.1-70B on BFCL.** → For our 3-bit model this is the BIGGEST win: force the tool-call grammar → guaranteed valid native tool JSON, every time. We BUILT this (#32/#45 grammar-constrained tools). WIRE IT into the serve/gateway tool path. Higher leverage than healing alone.

### Local-model-as-agent-backend = a solved pattern (LiteLLM is the standard)
LiteLLM = standard proxy: Anthropic front + OpenAI back, route-by-model-name, point Claude Code/Cursor/Codex/Aider at ONE proxy → one local model. **Pin ≥1.83.0** (supply-chain incident 1.82.7-8, Mar 2026). Ollama v0.14.0 (Jan 2026) + LM Studio now ship native Anthropic Messages endpoints; **oMLX** solved the Mac RAM ceiling. → Our agent_gateway.py is a lean zero-dep equivalent (keep it; LiteLLM if we want routing/scale).

### Tool-use SFT data for #114 (teach native emission)
Datasets: xLAM-function-calling-60k (Salesforce), glaive-function-calling-v2, ToolACE, ToolMind, APIGen-MT, When2Call. Hammer = function-masking for on-device. QLoRA on xLAM is the standard recipe. → ADD these to the #114 heal so the model learns WHEN/WHAT to call (complements constrained decoding's HOW).

### NATIVE-TOOLS PLAN (3 complementary levers, all ours to pull):
1. **Constrained decoding (#45)** → guarantees valid tool JSON (helps small models MOST) — HIGHEST leverage, wire now.
2. **Restored template (DONE) + parser** (gateway parse now; add GLM parser to mlx-lm or adopt Rapid-MLX for true mlx-native).
3. **Tool-use SFT** (xLAM/glaive into #114) → teaches when/what to call.
