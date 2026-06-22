---
license: mit
language: [en]
task_categories: [text-generation]
tags: [code, verified, agentic, mlx, glm, distillation, heal, lora, soul-canon, calibration]
size_categories: [100K<n<1M]
pretty_name: GLM-5.2 Demolition — Verified Code Gold, Soul Canons & Calibration
---

# GLM-5.2-Demolition — Training & Calibration Data

The data behind [`philipjohnbasile/GLM-5.2-Demolition-q4a4-soul-MLX`](https://huggingface.co/philipjohnbasile/GLM-5.2-Demolition-q4a4-soul-MLX).
**272,549 examples (~1.05 GB)** across three uses: LoRA-heal gold, swappable-soul gold, and prune calibration.

> **Why this dataset matters more than the weights.** A measured finding of the project (see the model's
> `MISSION_SUMMARY.md`): *the data re-derives the adapters; the adapters re-derive from nothing.* The weights
> are a disposable artifact of one base — **this data is the reusable asset**, and it carries over to heal any
> clean base (e.g. Qwen3-Coder-30B).

## Contents

| Group | What | Use |
|---|---|---|
| **heal/ gold** (vanilla FOCUS-9) | verified code in Python · TypeScript · JavaScript · Rust · Go · HTML · CSS · SQL · Postgres — **vanilla, latest versions, no frameworks** | LoRA-heal the pruned base back to coherence |
| **heal/souls_\*** | heritage "soul" gold per facet — security, science, legacy, design, art, music, perfumery, fullstack, gamedev | per-facet swappable LoRA adapters (the "model factory") |
| **calib/** | calibration corpus (incl. `reap_mix.jsonl`) | REAP saliency — which experts to keep when pruning |

- **Format:** JSONL, OpenAI chat schema (`{"messages":[{"role","content"},...]}`).
- **Verification:** the code gold is flywheel-generated and **verifier-checked** (compiled/tested via the
  pipeline's `src/verifiers.py`) — not scraped, not unchecked model output.
- **FOCUS-9 + souls split:** the *core* is pure vanilla FOCUS-9; everything applied (frameworks, specialties)
  lives in the swappable **soul** gold, never the core.

## Provenance & honesty
- Distilled/flywheeled from the MIT-licensed [`zai-org/GLM-5.2`](https://huggingface.co/zai-org/GLM-5.2)
  pipeline, filtered to vanilla FOCUS-9 + verified.
- Known gaps logged honestly: Go/JS vanilla gold is thinner than Python; the security-soul heal measured
  *neutral-to-degrading on the demolished base* (it's gold for a clean base, not a proven lift on the artifact).

## How to use
```python
from datasets import load_dataset
ds = load_dataset("philipjohnbasile/glm52-demolition-data", data_files="heal/**/*.jsonl")
```
Heal a clean base with the FOCUS-9 gold, mount a soul from `heal/souls_*`, or reuse `calib/` to prune your own MoE.

## License
MIT (GLM-5.2 is Z.ai "Pure Open"). Attribute Z.ai + this repo if you build on it.
