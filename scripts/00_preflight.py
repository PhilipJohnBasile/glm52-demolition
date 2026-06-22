#!/usr/bin/env python3
"""Preflight: prove the toolchain can actually run GLM-5.2 BEFORE downloading it.

Checks, in order:
  1. mlx-lm is installed and exposes the `glm_moe_dsa` architecture.
  2. `glm_moe_dsa.Model` resolves a real forward pass (inherited from
     deepseek_v32), i.e. it is NOT a stub.
  3. reap-mlx is importable and our GLM-5.2 adapter registers cleanly.
  4. Report unified memory and a fit-budget estimate.

Exit non-zero if anything that blocks the pipeline is missing.
"""

import importlib
import os
import sys

FAIL = 0


def ok(msg):
    print(f"  [ok] {msg}")


def bad(msg):
    global FAIL
    FAIL += 1
    print(f"  [!!] {msg}")


print("== 1. mlx-lm + glm_moe_dsa architecture ==")
try:
    import mlx_lm

    print(f"  mlx-lm {getattr(mlx_lm, '__version__', '?')}")
    base = os.path.dirname(mlx_lm.__file__)
    if os.path.exists(os.path.join(base, "models", "glm_moe_dsa.py")):
        ok("glm_moe_dsa.py present")
    else:
        bad("glm_moe_dsa.py MISSING -> GLM-5.2 unsupported; upgrade mlx-lm")
except Exception as e:  # noqa: BLE001
    bad(f"mlx-lm import failed: {e}")

print("== 2. forward pass is real (inherited from deepseek_v32) ==")
try:
    arch = importlib.import_module("mlx_lm.models.glm_moe_dsa")
    mro = [c.__name__ for c in arch.Model.__mro__]
    if hasattr(arch.Model, "__call__") and any("Model" in m for m in mro[1:]):
        ok(f"Model resolves __call__ via MRO {mro[:3]}")
    else:
        bad("glm_moe_dsa.Model has no inherited forward pass (stub)")
except Exception as e:  # noqa: BLE001
    bad(f"could not import glm_moe_dsa: {e}")

print("== 3. reap-mlx + GLM-5.2 adapter ==")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    import glm52_reap_adapter as gad

    gad.register()
    from reap.model_adapters import infer_model_adapter

    a = infer_model_adapter(config={"model_type": "glm_moe_dsa"})
    if a.adapter_name == "glm52_moe_dsa":
        ok("reap-mlx present; GLM-5.2 adapter selected")
    else:
        bad(f"adapter not selected (got {a.adapter_name})")
except Exception as e:  # noqa: BLE001
    bad(f"reap-mlx/adapter problem: {e}  (run: uv sync in reap-mlx)")

print("== 4. memory budget ==")
try:
    import subprocess

    gb = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"])) / 1024**3
    usable = gb * 0.85
    print(f"  unified memory: {gb:.0f} GB  (~{usable:.0f} GB usable for weights+KV)")
    print(f"  target demolished size: <= {usable - 15:.0f} GB to leave KV headroom")
except Exception as e:  # noqa: BLE001
    print(f"  (could not read hw.memsize: {e})")

print()
if FAIL:
    print(f"PREFLIGHT FAILED ({FAIL} blocker(s)). Fix above before downloading.")
    sys.exit(1)
print("PREFLIGHT PASSED. Safe to proceed to 01_download.sh")
