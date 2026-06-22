# 10-Round Deep Research: how to make the demolished GLM-5.2 better (June 2026)

Goal: "constantly research how to make this better." 10 rounds, ~40 searches, every claim sourced.
Context: v5c (saliency affine, 6-bit heads) measured at 99 GB / **5.3 tok/s** (1.47× v4) / coherent — the
working base. The shipped model stays q3a4-v4+soul2 until a heal validates v5c.

## The 10 rounds (one line each)
1. **Bit-allocation** — KL-guided (SliM-LLM) is optimal; use an **imatrix** (⟨a²⟩ activation importance), allocate **per-tensor** (ffn_down protected, ffn_up/gate aggressive), keep **router + shared experts high-precision**.
2. **Heal/recovery** — **QAD** (KL-distill teacher→student) > SFT; **SPEQ** makes the student its own teacher (no FP teacher needed); **Recover-LoRA** = 80–95 % 2-bit recovery from 10k synthetic; rank 64–128, lr 3e-4, α=2r; anti-repetition data fixes degeneration.
3. **Speed** — NVFP4 is **0 speedup in mlx** (Ollama-only); the real levers are a custom kernel or trellis serving.
4. **Frontier quant** — **QTIP (trellis + incoherence)** is SOTA but CUDA-only; **rotation (SpinQuant > QuaRot)** suppresses outliers.
5. **Rotation/incoherence** — Hadamard rotation **before** quant → outlier-free → fixes 3-bit collapse at the quant level; **feasible on MLX** (PolarQuant); makes the forward *faster*. **Biggest quant lever.**
6. **Serving** — **PonyExl3 (EXL3 trellis on MLX)** measured **152 tok/s on a 27B / M5 Max**, MoE+LoRA+spec support; **Self-Speculative MoE = 3.72×** (our "spec dead" was naive-spec only).
7. **Agentic quality** — **the SCAFFOLD matters MORE than the model** (11–50 pt swings); **Agent-RLVR = +13–18 pts SWE-bench**; small model + elite scaffold beats big model.
8. **Context** — our **DSA *is* DeepSeek's** (1M ctx @ 9.62 GiB KV); **int4 KV-cache is FREE on Apple Silicon** (outruns fp16); hybrid retrieval+long-ctx (our CallSieve+DSA).
9. **Reliability** — our stack (100 % constrained tool-JSON, verified decode, verifier mesh) **IS the validated SOTA**; upgrades = SCoRe self-correction RL, GenPRM, multi-verifier.
10. **Compression** — REAP (ours) is SOTA (+ Mar-2026 renorm fix); order **P→KD→Q** is best; Unsloth Dynamic 2.0 beats imatrix+QAT on KL.

## PRIORITIZED ACTION PLAN (impact × feasibility)

### 🔴 Tier 1 — highest impact, do first
1. ~~**Hadamard rotation before quant**~~ — **MEASURED DEAD for our stack (2026-06-19).** GPU-free prototype: rotation is **0.94–1.00× (slightly *worse*)** on mlx group-wise 3-bit (group 32/64/128), worse as the group shrinks. The research benefit is for *per-tensor / activation* quant — which mlx doesn't even support (max group 128, by design). Skip it. *The "measure the lever before the GPU job" discipline saved a wasted run — the nvfp4 lesson applied.*
2. **QAD heal** (R2) — KL-distill from the **mxfp4 teacher** (or SPEQ self-teacher) into v5c; recovers the 2-bit loss (80–95 %) and the CKA term fights collapse. Replaces plain-SFT heal. *The real quality lever (the collapse fix is the heal, not the quant — measured).* 
3. **imatrix + per-tensor saliency** (R1) — replace depth-U with ⟨a²⟩ importance; protect `ffn_down` + router + shared experts; aggressive 2-bit on `ffn_up/gate`. Better allocation at the same size.
4. **KL-eval (#60)** (R1/R10) — the gold metric to *validate* every change (Unsloth's bar). Build + run on v4/v5b/v5c. *Without this we're guessing.*

### 🟠 Tier 2 — big wins, more effort
5. **EXL3/PonyExl3 trellis serving** (R6) — better quant (trellis) + fused in-kernel decode, measured fast on M5. Evaluate converting our model.
6. **int4 KV-cache quant** (R8) — free on Apple Silicon, 3× KV compression. Wire into the serve (supersedes #86 SSD-offload).
7. **Self-Speculative MoE / layer-skip** (R6) — 3.72× decode, no draft model. Re-open #69 with the MoE-specific method.
8. **Long-context via DSA + YaRN** (R8) — our DSA already does 1M cheaply; extend RoPE (400–600 steps). Turns our weakest axis into a strength.

### 🟢 Tier 3 — strategic (compounding)
9. **Agent-RLVR** (R7) — execution-reward RL with guidance → +13–18 pts SWE-bench. Upgrade #18.
10. **Double down on the SCAFFOLD** (R7) — the harness drives 11–50 pts; our verify-everything is the right bet — invest there over chasing raw model size.
11. **Compression order P→KD→Q** (R10) — for any future demolition, heal the pruned model *before* quantizing.

## What this changes immediately
- The **#59 heal** (next GPU job) should be **QAD (KL-distill), not plain SFT**, with anti-repetition data — Tier-1 #2.
- Before the heal, **prototype Hadamard rotation** (Tier-1 #1) — it may fix the collapse cheaper than the heal.
- **Build #60 KL-eval first** — so we measure, not guess (the lesson of the nvfp4 mistake).

*Sources: per-round inline above — Unsloth Dynamic-v2, QTIP (2406.11235), SpinQuant (2405.16406), PolarQuant (2603.29078), QAD (2601.20088), SPEQ, Recover-LoRA (2606.04238), PonyExl3, SS-MoE (3792218), Agent-RLVR (2506.11425), scaffold-taxonomy (2604.03515), DeepSeek-V4 DSA, int4-KV (2605.05699), XGrammar-2 (2601.04426), REAP (2510.13999), compression-order (2603.18426).*
