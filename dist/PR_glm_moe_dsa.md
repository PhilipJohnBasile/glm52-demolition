# PR: Add `glm_moe_dsa` model support (GLM-5 / GLM-5.2)

**Target:** `ml-explore/mlx-lm` · **Closes:** #879 (and unblocks #277 / #806 downstream) · **File:** `mlx_lm/models/glm_moe_dsa.py`

## Summary
Adds a working model implementation for **`model_type: "glm_moe_dsa"`** — the architecture of Z.ai's
**GLM-5 / GLM-5.2** (744B sparse MoE). Today mlx-lm ships only a stub for `glm_moe_dsa`, so loading or
converting GLM-5.x fails with *"Missing parameters"*. This makes GLM-5.2 load and run natively in mlx-lm
(and therefore in LM Studio, Ollama-MLX, vllm-mlx, and every other mlx-lm-based runtime).

## The architecture
`glm_moe_dsa` is a **DeepSeek-V3.2-style** model: **MLA** attention + **DeepSeek Sparse Attention (DSA)**
(a lightning indexer that selects top-k KV positions) + a routed **MoE** (256 experts, 8 active). It is
nearly identical to `deepseek_v32`, which mlx-lm already supports — so this implementation **subclasses
`deepseek_v32`** and adds only what differs.

## What differs (the one real change)
The DSA **`indexer_types` (full / shared)** scheme. GLM places the lightning-indexer weights **only on
`'full'` layers**; `'shared'` layers **reuse the top-k indices** computed by the most recent full layer
(in groups of `index_topk_freq`). A naive port that builds an indexer on *every* layer fails to load
(the shared layers have no `indexer.*` weights). This PR:
- adds `indexer_types` / `index_topk_freq` to `ModelArgs`,
- builds the indexer only on full layers (`GlmDsaAttention`), and threads the shared-layer top-k
  indices forward (`GlmDsaDecoderLayer` / `GlmDsaModel`).

~255 lines, almost all of it thin subclassing of `deepseek_v32`.

## Optional: large-model streaming
The module includes an env-gated `GLM_STREAM_EVAL` (per-layer `mx.eval`) so a >RAM model can run on a
128 GB Mac via mmap paging. Happy to gate it off-by-default or drop it if preferred for upstream — it's
isolated behind the env var and does not affect correctness.

## Testing
- Loads + generates with **`zai-org/GLM-5.2`** and the community MLX quants (`mlx-community/GLM-5.2-mxfp4`,
  `pipenetwork/GLM-5.2-MLX-*`).
- Verified end-to-end serving via `mlx_lm.server` (OpenAI API) and downstream tool/agent use, including a
  Lean-4 theorem-proving workload (generation correctness under temperature).

## Notes
- Built on the existing `deepseek_v32` model — minimal surface area, easy to review.
- Co-developed while demolishing GLM-5.2 to run on a single 128 GB Mac (MIT, base model © Z.ai).
- Happy to add a unit test / convert-and-load smoke test in the style of the existing model tests if wanted.
