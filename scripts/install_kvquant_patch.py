#!/usr/bin/env python3
"""#117 INT8-KV on the M5 Neural Accelerator — expose mlx-lm's FREE QuantizedKVCache to the server.

mlx-lm 0.31.3 ships QuantizedKVCache + KVCache.to_quantized() but mlx_lm.server doesn't expose it. This
idempotent patch inserts an ENV-GATED monkeypatch of `make_prompt_cache` in server.py: when MLX_KV_BITS
is set, every cache is converted to quantized (group_size MLX_KV_GROUP, bits MLX_KV_BITS) → KV cache rides
the M5 NA INT8 fast path (~2× attention) + frees RAM + longer context. OFF by default (env unset) = the
server is byte-identical → zero risk. Mirrors install_glm_dsa_patch.py.

  python scripts/install_kvquant_patch.py --dry-run   # apply to a COPY, verify it imports (no live touch)
  python scripts/install_kvquant_patch.py             # apply to the live mlx_lm install (do at serve restart)
  MLX_KV_BITS=8 MLX_KV_GROUP=64 python -m mlx_lm.server ...   # then activate
"""
import os
import shutil
import subprocess
import sys
import tempfile

MARKER = "# --- #117 INT8-KV (M5 NA) env-gated patch ---"
ANCHOR = "from .sample_utils import make_logits_processors, make_sampler"
BLOCK = f'''
{MARKER}
import os as _os
if _os.environ.get("MLX_KV_BITS"):
    _kvb = int(_os.environ["MLX_KV_BITS"]); _kvg = int(_os.environ.get("MLX_KV_GROUP", "64"))
    _orig_make_prompt_cache = make_prompt_cache
    def make_prompt_cache(model, max_kv_size=None):          # noqa: F811  (env-gated override)
        _cs = _orig_make_prompt_cache(model, max_kv_size)
        return [c.to_quantized(group_size=_kvg, bits=_kvb) if hasattr(c, "to_quantized") else c for c in _cs]
# --- end #117 patch ---
'''


def server_path():
    import mlx_lm
    return os.path.join(os.path.dirname(mlx_lm.__file__), "server.py")


def patch_text(src):
    if MARKER in src:
        return src, "already patched"
    if ANCHOR not in src:
        return src, "ANCHOR not found (mlx-lm layout changed — patch needs review)"
    return src.replace(ANCHOR, ANCHOR + "\n" + BLOCK, 1), "patched"


def main():
    dry = "--dry-run" in sys.argv
    p = server_path()
    src = open(p).read()
    out, status = patch_text(src)
    if status not in ("patched", "already patched"):
        print(f"  ❌ {status}"); sys.exit(1)
    if dry:
        d = tempfile.mkdtemp()
        cp = os.path.join(d, "server.py")
        open(cp, "w").write(out)
        rc = subprocess.run([sys.executable, "-c", f"import ast; ast.parse(open('{cp}').read())"]).returncode
        print(f"  DRY-RUN: {status}; patched copy py-compiles: {'✅' if rc == 0 else '❌'} ({cp})")
        print(f"  (OFF by default — only active when MLX_KV_BITS is set; live install untouched)")
    else:
        shutil.copy(p, p + ".kvbak")
        open(p, "w").write(out)
        print(f"  ✅ {status} {p} (backup {p}.kvbak). Activate: MLX_KV_BITS=8 MLX_KV_GROUP=64")


if __name__ == "__main__":
    main()
