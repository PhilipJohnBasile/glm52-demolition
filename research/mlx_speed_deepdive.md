# Can we code MLX ourselves for more decode speed? (June 2026 deep dive)

**Question:** the agentic coder's one weakness is decode speed (~11–14 tok/s). Can custom MLX/Metal code beat it?

## The wall (unchanged, re-confirmed)
Decode is **memory-bandwidth-bound** — generation speed ≈ *bytes moved per token* (every token streams the active
expert weights through the memory bus). TTFT is compute-bound (and the M5 fixes that); decode is not. Our **#33 fused
MoE dequant-matmul Metal kernel already IS the 11–14 tok/s** — it maxed the compute side. You cannot out-*compute*
bandwidth. "More speed" = fewer bytes/token, or faster per-byte processing on M5 hardware.

## Lever 1 — NVFP4 on the M5 hardware path *(MEASURED DEAD in mlx — corrected 2026-06-19)*
- **The 2× was Ollama's, NOT mlx's.** `mx.quantize(mode="nvfp4")` works and `mx.quantized_matmul(mode="nvfp4")` is
  *correct* (rel-err 0.10) — but it is **not faster**. Measured decode-step matmul: affine-3b `264µs` · affine-4b `260µs`
  · **nvfp4 `262µs`** · mxfp4 `262µs` — all identical. The M5 hardware NVFP4 path lives in **Ollama 0.19's**
  NVIDIA-contributed kernel, **not** in mlx's `quantized_matmul`. NVFP4-in-mlx gives **zero speedup**.
- **And it broke serving:** building #59 with `--nvfp4` gave a model at **1.3 tok/s + garbage output** — mlx_lm doesn't
  pass the per-module `mode` to `nn.QuantizedLinear` (which *does* support it), so nvfp4 weights get dequantized as
  affine → corruption. Fixable, but pointless since there's no speed gain.
- **Round-trip fidelity is still real** (nvfp4-4b err 0.077 vs affine-3b 0.159) — but moot: you can't serve it faster.
- **Verdict:** run the saliency plan in plain **affine** (the *collapse fix* — early/late at 4-bit — still works, served
  correctly). The decode speedup is NOT here → Lever 2 (custom kernel) or route serving through Ollama 0.19's backend.

## Lever 2 — a Metal-4 **TensorOps** fused-MoE kernel *(the "code it ourselves" win, ~30–60%)*
- **#33's kernel predates the M5** — it uses plain Metal, not the **Neural Accelerators' hardware matmul** (Metal 4
  TensorOps). MLX gets 30–60% on M5 by using TensorOps; a *custom* MoE kernel that does too captures that for our model.
- **How:** `mx.fast.metal_kernel` + Metal 4 **TensorOps** — slice the gather'd expert weights into tiles, tile-wise
  matmul on the Neural Accelerators, keep data in cache (WWDC26 session 330 "Optimize custom ML operations with Metal
  tensors" is the recipe). Fuse: expert-gather → NVFP4-dequant → matmul → accumulate, in one dispatch.
- **Effort:** real Metal work (~weeks). Reference impls exist (TurboQuant-MLX fused kernels; simdgroup-MMA int4-MoE kernels).

## Honest ceiling
Neither lever breaks the bandwidth wall — they reduce bytes (NVFP4) and speed per-byte (TensorOps on the Accelerators).
Realistic: **11–14 → ~20–28 tok/s** from NVFP4+M5 alone; **~30+** with the custom TensorOps kernel. A genuine **2–3×**,
not 100+. Speculative decode stays dead on this MoE (any multi-token verify reloads ~all experts — the bandwidth wall again).

## Plan (CPU now → GPU later)
1. **NVFP4 re-quant** — wire `nvfp4` (group 16) into `04b`/`24b` as the 4-bit-layer format for #59; re-quant; **measure decode** (the proof).
2. If the gain lands and we want more → **write the Metal-4 TensorOps fused-MoE kernel** (the 30–60% lever); benchmark vs #33.
3. Keep the verify-everything stack (constrained decode, compiler-steer) intact — none of this touches it.

*Sources: MLX custom Metal kernels (ml-explore docs 0.31.2) · `mx.fast.metal_kernel` · WWDC26 #330 Metal tensors ·
Apple "LLMs with MLX + M5 Neural Accelerators" · TurboQuant-MLX fused kernels · MLX-vs-llama.cpp M5 benchmarks (yage.ai 2026) · our SPEED.md root-cause.*
