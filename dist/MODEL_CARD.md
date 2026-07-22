> ⚠️ **Describes an earlier version (v1: 3-bit / 99 GB).** Current = **v3: 4-bit / ~98 GB, HumanEval-164 = 69%, now PUBLIC** (https://huggingface.co/philipjohnbasile/GLM-5.2-Demolition-q4a4-soul-MLX, MIT). Canonical truth: `MODEL_CARD_v3.md` + `MISSION_SUMMARY.md`.

---
license: mit
base_model: zai-org/GLM-5.2
library_name: mlx
pipeline_tag: text-generation
language: [en]
tags: [mlx, moe, code, agentic, glm, pruned, quantized, verified-decoding, apple-silicon, local-agent]
---

# GLM-5.2-Demolition — a 743B frontier MoE, demolished to run on a 128 GB Mac

**One line:** we took `zai-org/GLM-5.2` (743B-parameter Mixture-of-Experts, ~381 GB at 4-bit) and
demolished it to **99 GB** so it runs **fully on-device on a MacBook Pro M5 Max (128 GB)** — then
healed it and wrapped it in a **51-tool local agent** that does things a cloud model structurally
cannot: the **compiler steers every line it writes**, it **can't fake a passing test or leak a
secret**, and it can be **fine-tuned on *your* private repo** so it writes in your style.

A **niche specialist**, not a general model — tuned to beat a frontier model *in one lane* (agentic
coding + design for **TS/JS/Python/Rust/Go/HTML/CSS** + Postgres) by out-*verifying* it, not out-knowing it.

## How it was made
1. **Pruned** the MoE experts 256 → 77 by **router-weighted saliency (REAP** = `router_weight ×
   activation_norm`, padding-masked), streaming layer-by-layer (~5 GB working set — it never fits in RAM).
2. **Quantized** mixed-precision (MLX): experts **3-bit**, attention/embeddings/lm_head **4-bit** → **99 GB**.
3. **Healed** with **LoRA SFT** (`--no-mask-prompt`, grad-checkpointed). The current **v4** rebuild uses a
   **code-first balanced calibration** (so the *math* super-experts survive the prune — v3's coding-only
   calibration collapsed math) + heal/distill on **R1 long-CoT reasoning traces**. Router-KD / expert-wise
   Logit-KD are research-validated recovery stages (optional). *(GRPO/RLVR was tried and regressed → SFT.)*

## What makes it different (built + selftested)
- **Verified decoding (compiler-steered):** generates line-by-line while the **real type-checker runs in
  the loop**; a line that adds an error is backtracked. TS 0.3 ms · Python ~0 ms · Rust 34 ms per check.
  Practical *only* on Apple Silicon — unified memory lets the model (GPU) and compiler (CPU) share RAM.
- **The verifier mesh:** every output meets its real tool — compile+run+**idiomatic lint** (clippy/ruff/
  gofmt/prettier) for 5 langs, **SQL** (sqlite), **math** (SymPy), **proofs** (**Lean 4**), design (render+see).
- **A 51-tool agent** with **five defense layers** the frontier lacks out of the box:
  **trust** (checkpoint/rollback, secret-scan, prompt-injection guard, audit, risk-gate),
  **reliability** (constraint-pinning vs context-rot, false-success guard, flaky-test re-run, onboarding map),
  **self-improvement** (skill library, large-output pointers, clarify-before-assuming),
  **integrity** (test-tamper guard, fabrication-proof `done`, scope enforcement, slopsquat guard),
  plus a **humanizer** (kills AI-slop, matches your voice).
- **Own your repo:** `scripts/64_own_your_repo.py` fine-tunes the model on *your* private codebase so it
  writes in your style — a cloud flagship can't be tuned on your private code.
- **Design soul** (render-and-measure critic: WCAG/type-scale/OKLCH), **CallSieve** zero-token retrieval +
  live-docs RAG, **vision/voice/video** (all MLX), code-rendered math/arch figures (matplotlib/manim/TikZ).

## Every chip on the M5 Max, working
The agent spreads perception, verification, and dispatch across **all six compute blocks** so the GPU stays
free for token generation (built + selftested):
- **GPU** (40-core + M5 Neural Accelerators) — the 99 GB model decodes + LoRA-heals.
- **Neural Engine** (16-core) — embeddings · OCR · image segmentation / pose / object-detection · NER+POS ·
  audio classification + VAD · neural TTS · zero-shot routing · rerank — all via Apple frameworks, no CoreML, no GPU.
- **18 CPU cores** — the verifier mesh fanned out (`verify_many`, 6.6×) · 9-language compile-verify · tabular ML.
- **Media Engine** — hardware H.264/HEVC/AV1 decode + encode for the video lane.
- **AMX/SME** — matrix coprocessor via Accelerate (~2.1 TFLOP/s f32), implicit in every numpy op.
- **ASR** = **Whisper on MLX** (no mic-permission needed). An **Any-to-Any omni-router** sends any input
  (text / image / audio / video / table) to its optimal block.

## The model factory (swappable domain souls)
One 99 GB base + hot-swappable LoRA "souls" (**~1.9 GB each** as the final adapter — the MoE LoRA spans many experts; MoE-Sieve will cut this to ~500 MB, see backlog) — change the model's specialty by swapping the
adapter: **code · design · agentic · gamedev · legacy/enterprise · security · fullstack · science · data ·
perfumery**. Each is healed from the same base by an autonomous chain that forges the whole library overnight
on the one Mac — and a `factory`-dispatcher soul makes the model route requests to the right specialty itself.

## Requirements
- **Apple Silicon, 128 GB** unified memory (M5-class recommended), macOS 26/27+. **MLX ≥ 0.31.**
- The architecture (`glm_moe_dsa`: MLA + DSA sparse attention) needs the **bundled patches** — stock
  mlx_lm can't load it.
- **⚠️ Raise the GPU memory ceiling — required.** The model needs ~101.6 GB; macOS caps the GPU
  working set at ~110 GB by default, so it OOM-crashes (Metal command-buffer timeout) on long
  generations. Fix before serving:
  ```bash
  sudo sysctl iogpu.wired_limit_mb=122000        # 122 GB; one-shot (resets on reboot)
  sudo bash dist/install_gpu_limit.sh            # OR: persist it via a LaunchDaemon
  ```
  Without this the model appears to "randomly crash" — it's just memory-starved.

## Use it
```bash
python dist/install_glm_dsa_patch.py          # patch mlx_lm (venv AND LM Studio's bundled engine)
GLM_STREAM_EVAL=0 python -m mlx_lm.server --model models/GLM-5.2-q3a4-v4 \
    --adapter-path heal/adapters-v4           # serve (OpenAI-compatible); v2 + heal/adapters also ship
# drive the 51-tool agent on your repo:
python scripts/57_tool_agent.py --repo /path/to/your/repo --apply --task "..." --test "cargo test"
# speed: try --dsa-block-size 32/64/128 (free, pick fastest). External draft is Metal-unstable here.
# (Update: MTP self-spec, called "the real path" in an earlier version of this line, was later
#  gated at 0% accept -- see SPEED.md. No speculative path is live; batching is the speed lever.)
```
In **LM Studio**: run the patch, fully quit + reopen, then load the model.

## Performance (M5 Max 128 GB, v4)
*Why this is special — the full positioning (a datacenter-only 744B model running on one laptop, fully cited): [`research/WHAT_MAKES_US_SPECIAL.md`](../research/WHAT_MAKES_US_SPECIAL.md). The short version: the ecosystem treats GLM-5.2 as 8×H200 / 376 GB-Q4 territory; we run it at 99 GB on one Mac, self-healing from real (programmatic, un-gameable) verifiers.*
| Metric | Value |
|---|---|
| Size | 99 GB (from 381 GB mxfp4 / ~1.5 TB bf16) |
| HumanEval pass@1 | **116/164 (70%)** — full HumanEval-164, single-shot, hidden-test scored, on the *souled* artifact *(supersedes an earlier 19/20 n=20 sample that ran fluke-high; the un-souled v3 base measures 114/164 = 69% — the README badge number)* |
| Math GSM8K | *⚠️ withheld — inconsistent across runs (8/12 here, 0–1/12 in later logs; harness-confounded). Pending a clean rerun before we publish a number.* |
| Algebra (SymPy-checked) | *⚠️ withheld — 2–3/4 across runs; same caveat.* |
| Decode speed | **11.3 tok/s** (no draft) — see the speed note in limitations |
| Verified-decode checker | TS 0.3 ms · Python ~0 ms · Rust 34 ms |

## Honest limitations
- **Specialist:** ~70% of experts pruned — strong in the target niche, weaker outside it. Not the full 743B.
- **Speed ~11 tok/s decode** (reading pace; ~3 min for long thinking-ON answers). Partly MLX's still-naive
  **DSA attention kernels** (mlx #837 / #3402 — *improves for free* as MLX matures), partly the bandwidth
  cost of a 743B-class MoE on a laptop. **Measured dead-ends** (don't bother): 4-bit re-quant is *slower*
  for single-token decode (bandwidth-bound, smaller wins); active-experts 8→4 gives no win at batch=1.
  **Real path (re-mapped June 2026, web-verified):** the MoE matmul + M5 accelerators are *already* optimal in
  MLX 0.31.2 (we ride `gather_qmm` + the M5 tensor path — 11 tok/s is genuine, not a misconfig).
  ~~Remaining levers: **MTP self-speculative** — our accept-rate gate (`89_mtp_gate.py`) is built; honest
  expectation is **~1.1–1.5× on a quantized MoE, NOT the 2.6×** of full-precision~~ — **measured after this
  was written: the gate ran and MTP self-spec scored 0% accept** (the un-pruned native head mismatches the
  pruned router — receipts in SPEED.md), so that lever is dead. The remaining upstreamable frontier is a
  true-sparse **DSA-prefill kernel**. Not a quant change.
- **Multilingual** ability reduced (optional vocab-trim drops ~31% of tokens).
- **Design** is competent but not yet design-soul-elite (correct structure, but missed OKLCH/grid when
  tested) — the design-canon heal closes this.
- Prompt-cache can OOM under heavy concurrent load. The external speculative draft is **Metal-unstable**
  on this MoE — **MTP self-speculative is the right path**; the external draft is not recommended.

## Attribution & license
**MIT.** Base model © **Z.ai** (`zai-org/GLM-5.2`, MIT-licensed) — so this derivative is MIT too: free
to use, modify, and redistribute **with attribution to Z.ai**. The demolition / healing / 51-tool agent
tooling is this repo's contribution.
