# GLM-5.2-Demolition — Workspace Customizations and Guidelines

This file defines project-scoped rules and instructions for agents working on the `GLM-5.2-Demolition` codebase.

---

## 1. Project Overview & Architecture
GLM-5.2-Demolition is a project aimed at taking the 743B-parameter Mixture-of-Experts (MoE) model `zai-org/GLM-5.2` (~381 GB at 4-bit) and pruning/quantizing it to **99 GiB (~106 GB)** to run fully on-device on a 128 GB MacBook Pro M5 Max. It includes LoRA healing, a local 51-tool ReAct agent, compiler-steered decoding, design-soul generation, and formal Lean 4 verification.

### Key Components & Directories:
- `src/`: Core logic modules.
  - [constrained_decode.py](../src/constrained_decode.py): Steered/constrained line-by-line decoding.
  - [verifier_mesh.py](../src/verifier_mesh.py) & [verifiers.py](../src/verifiers.py): Multi-language/tool execution and lint checking.
  - [trust.py](../src/trust.py): Security scan, secret scanner, and prompt injection guards.
  - [dynamic_bits.py](../src/dynamic_bits.py): Importance-weighted dynamic quantization allocator.
  - [stability.py](../src/stability.py) & [serve_stable.py](../scripts/serve_stable.py): Memory-capped stable serving setup.
- `scripts/`: Execution scripts for demolition, healing, evaluation, and agents.
  - [57_tool_agent.py](../scripts/57_tool_agent.py): The main 51-tool ReAct agent loop.
  - [41_verified_decode.py](../scripts/41_verified_decode.py): Live verified decoding driver.
  - [86_scoreboard.py](../scripts/86_scoreboard.py) & [87_lean_study.py](../scripts/87_lean_study.py): Scoreboard tracking and contamination-clean Lean study loop.

---

## 2. Coding & Implementation Guidelines

### A. Maintain Path and Executable Safety
- **No bare `python` execution**: Always use `sys.executable` in subprocesses instead of a bare `python` command to ensure the correct environment interpreter is used (avoiding path/venv mismatch).
- **Sandbox boundaries**: The agent sandbox checking must always use full-path comparisons with subdirectory delimiters (`full != repo_real and not full.startswith(repo_real + os.sep)`) to prevent sibling-directory escape bypasses.

### B. Stable MLX Serving & GPU Memory Safety
- The model requires ~101.6 GB. The GPU memory ceiling must be raised on macOS using:
  ```bash
  sudo sysctl iogpu.wired_limit_mb=122000
  ```
- Always ensure MLX memory limits are set using `mx.set_memory_limit` (wired in `stability.py` / `serve_stable.py`).
- Run the server with `GLM_STREAM_EVAL=0` to avoid per-layer paging overhead since the model fits entirely in 128 GB.

### C. Design Soul & Visual UI Verification
- Prepend the `CANON` system prompt from [design_canon.py](../src/design_canon.py) for all design/UI generation tasks.
- Avoid framework templates (Bootstrap/Tailwind) unless explicitly requested. Use oklch-only colors, modular type scales, 8px grid alignments, and custom animations.
- Design verifier gates (`audit_design`) must strip HTML/CSS comments before parsing to avoid comment false-positives, and must bound regex px quantifiers (`\d{1,7}`) to avoid ReDoS on long digit repeats.

### D. Security & Key Scanning
- The secret scanner in [trust.py](../src/trust.py) scans for modern formats including `sk-proj-` (with hyphens), `hf_`, `AIza`, and `sk_live_`. Keep regexes updated and clean.
- White-spaces and control chars must be normalized (`\s+`) before running the prompt-injection detector (`detect_injection`).

---

## 3. Tool Matrix (51-Tool ReAct Agent)
The agent integrates 51 specialized tools covering:
1. **AI Engineering**: prompt-cache, constrained decoding, dynamic-quant.
2. **Full-Stack**: compilers for TS/JS, Python, Rust, Go, C++; PostgreSQL, and browser render-measure checks.
3. **Data Science**: Jupyter notebook runner (`.ipynb`), SymPy, pandas, matplotlib/manim.
4. **Machine Learning**: REAP pruning calibration, LoRA SFT/distillation, and experimental tracking logs.
5. **System/Utility**: Local memory recall/store, fetch (raw requests), and diagnostic profiling.
