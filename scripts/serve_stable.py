#!/usr/bin/env python3
"""Stable MLX server (#47) — sets MLX's native memory guardrails BEFORE launching mlx_lm.server, so the
server SELF-BOUNDS (gracefully evicts instead of kernel-panicking) on long agentic runs. The framework
fix for the #883 unbounded-KV crash. Drop-in for `python -m mlx_lm.server ...`:

    GLM_STREAM_EVAL=1 python scripts/serve_stable.py --model models/GLM-5.2-q3a4-v4 \
        --adapter-path heal/adapters-lean --port 8080

Tunables: MLX_MEM_GB (default 118), MLX_CACHE_GB (default 8).
"""
import os
import runpy
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from stability import mx_set_limits  # noqa: E402

limits = mx_set_limits(memory_gb=float(os.environ.get("MLX_MEM_GB", 118)),
                       cache_gb=float(os.environ.get("MLX_CACHE_GB", 8)))
print(f"  [serve_stable] MLX self-bounding (evict, not crash): {limits}", flush=True)

# hand off to mlx_lm.server with the original CLI args
sys.argv = ["mlx_lm.server"] + sys.argv[1:]
runpy.run_module("mlx_lm.server", run_name="__main__")
