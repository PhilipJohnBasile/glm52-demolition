# Healing the demolished GLM-5.2 — research-backed playbook

Cerebras (REAP) publishes **no** post-pruning recovery. The 2026 literature does,
and it's the difference between "degraded" and "near-flagship on our slice." This
is our edge — especially critical because our ~70% prune is past REAP's proven
~25–50% envelope.

## What the research says (2026)

1. **Logit (KD) distillation > plain fine-tuning, decisively.** Recover quality by
   matching the *unpruned teacher's logits*, not just labels. Train with **forward
   KL divergence** (temperature-scaled, ×T²), LoRA-only to keep it cheap.
   *Recover-LoRA (EMNLP 2025); Minitron.*
2. **Expert-wise KD is the MoE standard.** Mixtral-8×7B at **50% sparsity recovers
   99%** of original performance via expert-wise knowledge distillation. *(arXiv
   2410.12013, 2506.18349.)*
3. **Router KD — cheap and MoE-specific.** Pruning changes which experts *should*
   be picked. Recalibrating **only the router** (freeze experts) recovers a lot for
   tiny cost. *("Necessity of Router Calibration," arXiv 2603.02217.)*
4. **Multi-stage prune+distill beats one-shot** with <10% of original data.
   *(SlimMoE, arXiv 2506.18349.)* → validates our iterative `03b`.
5. **Avoid catastrophic forgetting:** mix in ~**30–50% general/pretraining-style
   data** during healing, or the model collapses on anything off-distribution.
6. **Hyperparameters that work:** ~3 epochs, LR **2e-5**, **cosine** schedule w/
   warmup, forward-KL only during the recovery phase.

## The 128 GB problem (and the solution)

True logit distillation needs the **unpruned 743B teacher** running — which does
NOT fit 128 GB. Solution: **offline teacher logits**.
- Run the teacher **alone** over the calibration prompts; dump top-k logits to
  disk. (For the full model this needs a big box once, OR use the *less-pruned
  previous stage* as teacher — SlimMoE-style.)
- Train the student **alone** against the saved logits (KL). Never both in memory.
- **Iterative variant (what we do):** stage N−1 (healed) is the teacher for stage
  N. Each stage fits; logits are precomputed offline per stage. This is how a
  128 GB box does multi-stage distillation of a 743B model.

## Our healing stack (in priority order)

| Stage | Method | Status |
|---|---|---|
| 0 | **Router KD** — recalibrate router after each prune (freeze experts) | **BUILT** (`21_router_kd.py`): freezes all but gates (~9% params), validated |
| 1 | **DWQ** quantization = logit distillation of the quantized student | built (`04 --method dwq`) |
| 2 | **LoRA SFT** on verified + modern + your-repo data, anti-forgetting mix | **built** (`06`): cosine LR 2e-5, +35% general mix, mask-prompt |
| 3 | **Logit-KD LoRA** vs offline teacher logits (Recover-LoRA) | **BUILT** (`20_distill_heal.py`): offline dump + forward-KL train, validated |
| 4 | **Iterative** prune→heal→distill per stage (SlimMoE) | built (`03b`) |

## Recipe defaults (this repo)
- Heal data: ~60% specialized (verified-SFT + modern + your repos) + ~**35% general/
  reasoning** (anti-forgetting) + TS7 preference.
- LoRA: rank 16, **cosine LR** 2e-5→2e-6 with 100-step warmup, ~3 epochs-equiv.
- Run Router KD first (cheap), then SFT/logit-KD, fuse, eval, repeat per stage.

## Sources
- Recover-LoRA (arXiv 2510.08600) · Data-free post-pruning recovery (2511.20702)
- MoE-Pruner expert-wise KD (2410.12013) · SlimMoE (2506.18349)
- Router calibration necessity (2603.02217) · Minitron (2408.11796)

---
## v4 update (2026-06-17)
Biggest finding: the v3 REAP calibration was **coding-only**, which pruned the MATH
super-experts → math collapse (0/5 GSM8K, a known failure mode, arxiv 2507.23279).
**Fix in v4**: code-first BALANCED calibration (keeps code + math super-experts) +
heal/distill on **R1 long-CoT traces** (OpenR1-Math-220k — the DeepSeek-R1-Distill recipe)
via `scripts/62`→`06`. GRPO/RLVR was tried on v3 and REGRESSED (MoE-GRPO won't converge) → SFT.

---
## v4 recovery stack WIRED (2026-06-17, from June-2026 research)
Plain SFT under-recovers a heavily-pruned MoE. The validated stack (now in the v4 pipeline):
1. **Router-KD (`21`)** — *necessary*, not optional ([arxiv 2603.02217](https://arxiv.org/html/2603.02217),
   "The Necessity of Router Calibration"). Recalibrate the router to the kept (+quantized) experts.
   Runs on q3a4-v4 (99GB fits; the dsv32 stop_gradient fix handles the expert-gather VJP).
2. **SFT (`06`)** on heal/data-v4 — R1 long-CoT reasoning distillation (the R1-Distill recipe).
3. **Expert-wise Logit-KD (`20`)** — teacher = the unpruned pruned-v4, student = q3a4-v4-rc; forward-KL
   recovers prune/quant loss ([MoE-Pruner 2410.12013](https://arxiv.org/pdf/2410.12013), SlimQwen).
Each risky stage has an SFT fallback so the autonomous run can't stall. Validation: the agent HARNESS
is worth 30-50 pts on its own (Terminal-Bench 2.0) — our verification harness IS the edge.
