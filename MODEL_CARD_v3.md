---
license: mit
base_model: zai-org/GLM-5.2
base_model_relation: quantized
library_name: mlx
pipeline_tag: text-generation
language: [en]
tags: [mlx, apple-silicon, moe, pruned, quantized, soul-targeted, agentic, local-agent, glm]
private: false
datasets: [philipjohnbasile/glm52-demolition-data]
model-index:
- name: GLM-5.2-Demolition-q4a4-soul-MLX
  results:
  - task: { type: text-generation, name: Code Generation }
    dataset: { name: HumanEval, type: openai_humaneval }
    metrics:
    - { type: pass@1, value: 69.0, name: "pass@1 (HumanEval-164, single-shot, verifier-scored)" }
---

# GLM-5.2-Demolition · q4a4-soul (v3)

A **demolition** of [`zai-org/GLM-5.2`](https://huggingface.co/zai-org/GLM-5.2) (743B total / 39B active MoE,
MIT) down to a **~98 GB 4-bit** model that loads and runs **fully on a single Apple M5 Max (128 GB)**. v3's
distinguishing move is **soul-targeted expert pruning** — the kept experts are chosen by saliency measured on
*our* facet data, not a generic corpus — plus a deliberately **pure vanilla-code core** with **swappable
heritage "souls"** mounted on demand.

## Architecture: a PURE core + swappable souls
- **CORE (always-on):** *just the vanilla languages, done excellently* — Python · TypeScript · JavaScript ·
  Rust · Go · HTML · CSS · SQL · Postgres. **No frameworks, no baked specialties.** Latest versions, vanilla
  stdlib.
- **SOULS (mount per-request — the model factory):** small LoRA adapters that *name a field's masters* to
  activate latent eliteness:
  - **art** (Basquiat/Haring/Banksy/Sol LeWitt/Casey Reas) · **music** (Bach/J Dilla/Eno/WALL-E) ·
    **design** (Rams/Bauhaus) · **perfumery** (Beaux/Guerlain/Ellena) · **science** (Feynman/Darwin/Sagan) ·
    **legacy** (K&R/Knuth/Dijkstra/Hopper) · **security** (Saltzer-Schroeder/Aleph-One, purple-team) ·
    **gamedev** (Carmack/Handmade-Hero, *vanilla from-scratch*) · **fullstack** (htmx/Go-stdlib/Postgres) ·
    math · dataviz · prose · architecture · research.

## The demolition lineage (honest)
| ver | prune | quant | size | result |
|-----|-------|-------|------|--------|
| v1  | keep 30% experts (generic calib) | 3-bit | 99 GB | broke — hallucinates, sentence-loops |
| v2  | keep 23% experts (code calib)    | 4-bit | 98 GB | design coherent; trivia gone (by design) |
| **v3** | keep 23% experts (**soul calib**) | **4-bit** | ~98 GB | coherent FOCUS-9 vanilla code (healed) |

**Why 4-bit, not 3:** 3-bit was just below the quality cliff; 4-bit is just above it *and* MLX's best-optimized
kernel (cleanest packing). 2-bit is worse. No bit-width of a demolished 744B beats a clean right-sized model —
this artifact is the **best-possible demolition**, a research result, not a frontier claim.

## Method
1. **Saliency** (`23_stream_calibrate`) on our facet corpus → score each routed expert.
2. **Prune** (`24_apply_prune --ratio 0.77`) → keep the top-saliency experts.
3. **Re-quantize** (`24b_stream_requantize --bits 4`) → uniform 4-bit experts, 4-bit attn, 6-bit head.
4. **Heal** (`06_heal_lora`) — LoRA on vanilla FOCUS-9 gold; souls heal separately per facet.

## Honest scope
- **Speed:** ~11–14 tok/s single-stream — memory-bandwidth-bound (inherent to a 98 GB model on M5;
  spec-decode nets only ~1.05× here, so it's not used; receipts in [SPEED.md](SPEED.md). An earlier
  draft of this line said ~10).
- **Strengths:** the FOCUS-9 vanilla languages + whichever soul is mounted. **Not** general trivia — those
  experts were deliberately pruned. Best driven by a verifier-first agent (the compiler steers each line).
- **Eval:** **HumanEval-164 pass@1 = 114/164 (69%)** — full set, single-shot, scored on hidden tests by real
  verifiers (the easy n=20 subset was 95%). Mid-tier-usable for a demolished 4-bit model on a laptop
  (≈ GPT-4-class on this metric; below dedicated frontier coders ~90%); a verifier-first agent loop lifts it
  further. Strong on writing vanilla FOCUS-9 functions from a spec; weaker on hard debugging/multi-step and
  off-distribution prompts. **Honest scope:** this is the *best-possible demolition* of a 744B model, a research
  artifact — not a frontier daily-driver. See the full measured write-up in the repo's `MISSION_SUMMARY.md`.

Built with the open pipeline at `glm52-demolition`. **Public** (MIT — GLM-5.2 is Z.ai Pure-Open).
