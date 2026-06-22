# Restore / Reconstruct

This repo holds **only the code (~2.5 MB)**. The weights, data, and environment live elsewhere (by design —
never commit those to git). The local working directory can be safely deleted; everything below brings it back.

## What lives where

| Asset | Home | Restore |
|---|---|---|
| **Code** (pipeline, src, docs) | this GitHub repo | `git clone` |
| **Model** (~98 GB, q4a4-soul) | [HF model](https://huggingface.co/philipjohnbasile/GLM-5.2-Demolition-q4a4-soul-MLX) | `hf download` |
| **Training data** (272K verified examples) | [HF dataset](https://huggingface.co/datasets/philipjohnbasile/glm52-demolition-data) | `hf download` |
| **mxfp4 original** (381 GB) | re-derivable from [`zai-org/GLM-5.2`](https://huggingface.co/zai-org/GLM-5.2) | run the prune pipeline |
| `lean-verify/`, `rag/`, `.venv/` | not backed up | re-install / re-clone / `pip install` (trivial) |
| `logs/`, `research_index/` | local only (~7 MB, disposable) | not recoverable — but the real findings are in `MISSION_SUMMARY.md` / `OVERNIGHT_LOG.md` / `HEADTOHEAD_RESEARCH.md` here |

**Nothing of value is local-only.** Deleting the working dir loses only disposable runtime logs.

## Full restore

```bash
# 1. code
git clone https://github.com/PhilipJohnBasile/glm52-demolition
cd glm52-demolition

# 2. environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. training data (into ./heal and ./calib)
hf download philipjohnbasile/glm52-demolition-data --repo-type dataset --local-dir .

# 4. the model (only if you want to run it locally; ~98 GB)
hf download philipjohnbasile/GLM-5.2-Demolition-q4a4-soul-MLX --local-dir models/GLM-5.2-q4a4-v3
```

## The up-path (recommended over restoring the demolished model)

The demolished model is a research artifact at its ceiling. To actually *build* on this work, use the
model-agnostic core instead:

```bash
git clone https://github.com/PhilipJohnBasile/agent-toolkit   # verifiers, soul canons, flywheels
# then: heal a clean base (e.g. Qwen3-Coder-30B) with the HF dataset, drive it with merle
```

See `MISSION_SUMMARY.md` for the honest verdict and why.
