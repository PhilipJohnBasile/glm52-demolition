# GLM-5.2 Demolition 🧨

**Demolish a 743B frontier MoE down to ~98 GB so it runs *fully* on one Apple M5 Max (128 GB) — then heal,
soul-ify, and serve it with a verifier-first agent.**

[![Model](https://img.shields.io/badge/🤗_Model-q4a4--soul-yellow)](https://huggingface.co/philipjohnbasile/GLM-5.2-Demolition-q4a4-soul-MLX)
[![Dataset](https://img.shields.io/badge/🤗_Dataset-272K_verified-blue)](https://huggingface.co/datasets/philipjohnbasile/glm52-demolition-data)
[![HumanEval-164](https://img.shields.io/badge/HumanEval--164-69%25-green)](MISSION_SUMMARY.md)
[![License](https://img.shields.io/badge/license-MIT-black)](LICENSE)

> Takes [`zai-org/GLM-5.2`](https://huggingface.co/zai-org/GLM-5.2) (744B total / 39B active, MIT) → REAP
> soul-targeted expert prune → 4-bit MLX quant → LoRA heal → **~98 GB, HumanEval-164 = 69%, on a laptop.**

---

## What this is (honest)

A **research artifact + a reusable pipeline**, not a frontier daily-driver. The headline result is measured and
honest: a 744B model crushed to a quarter of its size still writes usable vanilla code (**69% pass@1 on the full
HumanEval-164**, real-verifier-scored). The deeper finding — *the demolished base is at its ceiling; the
**methods and data** are the transferable value* — is written up straight in **[`MISSION_SUMMARY.md`](MISSION_SUMMARY.md)**.

## Architecture: a PURE core + swappable souls

- **CORE (always on):** *just the vanilla languages, done well* — Python · TypeScript · JavaScript · Rust · Go ·
  HTML · CSS · SQL · Postgres. **No frameworks.** Latest versions, stdlib.
- **SOULS (mount per request — the "model factory"):** small LoRA adapters that *name a field's masters* to
  activate latent eliteness — design, art, music, perfumery, science, legacy, security, fullstack, gamedev.
  See **[`FACTORY.md`](FACTORY.md)** and **[`DESIGN_SOUL.md`](DESIGN_SOUL.md)**.

## The pipeline

| Stage | Script | What |
|---|---|---|
| 1. Saliency | `scripts/23_stream_calibrate.py` | score each routed expert on *our* facet corpus |
| 2. Prune | `scripts/24_apply_prune.py --ratio 0.77` | keep the top-saliency experts (REAP) |
| 3. Quantize | `scripts/24b_stream_requantize.py --bits 4` | uniform 4-bit experts/attn, 6-bit head (MLX) |
| 4. Heal | `scripts/06_heal_lora.py` | LoRA on vanilla FOCUS-9 gold; souls heal separately |
| 5. Serve | `scripts/serve_supervisor.py` | crash-safe `mlx_lm.server` + one mounted adapter |
| 6. Verify | `src/verifiers.py` | compile/test-check every generation (5 languages) |

## Results (measured, never faked)

- **HumanEval-164 pass@1 = 114/164 (69%)** — full set, single-shot, hidden-test scored (easy n=20 = 95%).
- **Speed:** ~11–14 tok/s single-stream — memory-bandwidth-bound (inherent to a 98 GB model on M5;
  spec-decode nets ~1.05×; receipts in [SPEED.md](SPEED.md). An earlier draft of this line said ~10).
- **The honest dead-lever map** (what *doesn't* work — saves you weeks): clean-base-beats-demolished,
  soul-heals-don't-lift-the-floor, spec-decode-~1.05×-on-M5. Full table in `MISSION_SUMMARY.md`.

## Artifacts

- **Model** (public, MIT): https://huggingface.co/philipjohnbasile/GLM-5.2-Demolition-q4a4-soul-MLX
- **Data** (272K verified examples + soul canons + calibration): https://huggingface.co/datasets/philipjohnbasile/glm52-demolition-data
- **merle** — the verifier-first coding CLI that drives it (separate public repo; model-agnostic via `MERLE_BASE`).

## Repurpose

Everything here carries over to a **clean right-sized base** (Qwen3-Coder-30B), where the data + souls *lift*
instead of merely holding the floor: heal a clean base with the FOCUS-9 gold, mount a soul, point merle at it.
That's the up-path — the methods on a model that fights back.

## Repo map

- `scripts/` — the numbered pipeline (calibrate → prune → quant → heal → serve → bench)
- `src/` — verifiers, the soul canons (`*_canon.py`), multimodal lanes, agent harness
- `MISSION_SUMMARY.md` — the honest measured verdict (read this first)
- `FACTORY.md` · `DESIGN_SOUL.md` — the swappable-souls architecture
- `MODEL_CARD_v3.md` — the canonical model card (= the HF README)
- `RESTORE.md` — how to reconstruct everything from GitHub + HF (the local dir is safe to delete)

## License

MIT. Built on `zai-org/GLM-5.2` (Z.ai "Pure Open", MIT) — attribute Z.ai. See [`LICENSE`](LICENSE).
