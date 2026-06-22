# Execution Queue — GLM-5.2-Demolition

Sequenced run-order for the parked work. **GPU-serial** (one at a time). After each item: log → scoreboard/card → next.
Times are generation-bound (~14 tok/s decode) → estimates, not promises. `#17` design-heal: ✅ done + shipped to HF.

---

## ▶ ORDER

### 1 · #71 — Batching (the speed lever) · ~4–5 h · **BUILD**
Wire continuous batching (#48) + batched best-of-N (#35) into `serve_stable` as the default mode, then extend
`scripts/45_bench_speed.py` to measure batch = 1 / 2 / 4 / 8 tok/s scaling.
**Done when:** the batch-scaling curve is logged (proves the throughput win — the *only* real speedup on this MoE).
**Why first:** it's the actionable conclusion of tonight's speed work, and concurrent benchmarking can ride on it.

### 2 · Benchmarks (real card numbers) · ~1–1.5 days · **mixed**
*Ready harnesses — run as-is (serve up):*
- **#63** HumanEval-164 + MBPP — `python scripts/58_bench.py --n 164` · ~1.5 h
- **#65** GSM8K-full + MATH — `python scripts/59_stem_diag.py` + `scripts/65_rft_math.py` · ~3–10 h
- **#68** Study→test (miniF2F, study⟂test proven) — `python scripts/87_lean_study.py` · ~3–4 h
- **#62** SWE-bench Verified (subset) — `python scripts/85_swebench.py --n 50` · ~8 h (full 500 ≈ days)

*Build the harness first (~1 h CPU each), then run:*
- **#67** GPQA Diamond + MMLU · **#66** LiveCodeBench · **#64** Aider Polyglot

All → `scripts/86_scoreboard.py` (contamination-checked) → unlock the card **model-index** once full-n lands.

### 3 · #51 — GGUF + llama.cpp DSA · ~2–4 h · **BUILD+RUN**
Convert q3a4 → GGUF (`llama-quantize` toolchain installed) → cover the non-MLX ecosystem.

### 4 · Family #53–58 (spread the recipe) · ~1–2 days · **LAST**
5 smaller sizes (67→55→36→20→14 GB) via `scripts/79_demolition_family.py` (prune→quant→heal each) +
`scripts/80_family_eval.py`. **#23** facet re-prune, **#59** dynamic-quant, **#60** KL-eval all baked in.

---

## ⛔ Skip
- **#69** fresh EAGLE-3 head — $4–15k / weeks-local, and *still* uncertain on this MoE. Not recommended.

## Runner
GPU-serial. Fire an item → an autonomous monitor watches its log → on clean completion: upload / scoreboard → fire the next.
Trigger phrases: **"wire batching"** (1) · **"run the benchmarks"** (2) · **"run gguf"** (3) · **"run the family"** (4).
A subset benchmark pass (#63 + #67 + #66) gives real card numbers in ~a few hours; the full suite + family is days.
