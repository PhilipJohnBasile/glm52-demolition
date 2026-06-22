#!/usr/bin/env python3
"""Put the GLM-5.2 DSA fix INTO every local mlx_lm — including LM Studio's
vendored backend — so the demolished GLM-5.2 loads WITHOUT depending on the
LM Studio app (closed source) shipping it.

The LM Studio *app* is closed, but the engine it loads MLX models with is
**open-source mlx_lm**, vendored on disk under ~/.lmstudio. Stock mlx_lm ships
only a 53-line stub for `glm_moe_dsa` (GLM-5.2's DeepSeek-Sparse-Attention MoE),
which is why GLM-5.2 fails to load ("Missing 285 parameters"). This script
overwrites that stub with our full 238-line implementation (full/shared indexer
handling), in place, with a one-time `.orig` backup.

  python dist/install_glm_dsa_patch.py            # patch every install found
  python dist/install_glm_dsa_patch.py --dry-run  # show targets, change nothing
  python dist/install_glm_dsa_patch.py --revert    # restore the .orig stubs

After patching, FULLY QUIT and reopen LM Studio so the backend reloads the engine.
"""
import argparse
import glob
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATCH = os.path.join(HERE, "glm_moe_dsa.py")
REL = os.path.join("mlx_lm", "models", "glm_moe_dsa.py")


def targets():
    found = set()
    home = os.path.expanduser("~")
    # scan EVERY common location an mlx_lm install may live, so we patch them ALL on this machine
    # (LM Studio, Ollama, conda/venv/virtualenv, project venvs, homebrew/usr-local/framework pythons)
    for g in [
        home + "/.lmstudio/**/site-packages/" + REL,          # LM Studio's vendored engines
        home + "/.ollama/**/site-packages/" + REL,            # Ollama (if it vendors mlx_lm)
        home + "/miniconda3/envs/*/lib/python*/site-packages/" + REL,
        home + "/anaconda3/envs/*/lib/python*/site-packages/" + REL,
        home + "/.conda/envs/*/lib/python*/site-packages/" + REL,
        home + "/.virtualenvs/*/lib/python*/site-packages/" + REL,
        home + "/.venv/lib/python*/site-packages/" + REL,
        home + "/*/.venv/lib/python*/site-packages/" + REL,   # project venvs under ~
        "/opt/homebrew/lib/python*/site-packages/" + REL,
        "/usr/local/lib/python*/site-packages/" + REL,
        "/Library/Frameworks/Python.framework/Versions/*/lib/python*/site-packages/" + REL,
    ]:
        found.update(glob.glob(g, recursive=("**" in g)))
    # plus the mlx_lm importable in THIS interpreter (pip/venv)
    try:
        import mlx_lm
        found.add(os.path.join(os.path.dirname(mlx_lm.__file__), "models", "glm_moe_dsa.py"))
    except Exception:  # noqa: BLE001
        pass
    return sorted(p for p in found if os.path.exists(os.path.dirname(p)))


# The deepseek_v32.py MoE fix that unblocks gradient-based RL (GRPO) on the
# quantized MoE: the routed expert indices are non-differentiable (GatherQMM VJP),
# so they must be stop_gradient'd. Targeted, idempotent patch.
DSV32_OLD = "inds = mx.argpartition(-scores, kth=k - 1, axis=-1)[..., :k]"
DSV32_NEW = ("inds = mx.stop_gradient(mx.argpartition(-scores, kth=k - 1, axis=-1)[..., :k])"
             "  # stop_gradient: MoE top-K indices non-diff (GatherQMM VJP); needed for GRPO")


def patch_dsv32(glm_target, dry_run=False, revert=False):
    """Patch deepseek_v32.py (same models/ dir as glm_moe_dsa.py). Idempotent;
    backs up .orig. Returns a status string or None if the file isn't there."""
    d = os.path.join(os.path.dirname(glm_target), "deepseek_v32.py")
    if not os.path.exists(d):
        return None
    if revert:
        if os.path.exists(d + ".orig"):
            shutil.copy(d + ".orig", d)
            return "reverted"
        return None
    src = open(d).read()
    if "stop_gradient(mx.argpartition(-scores" in src:
        return "already"
    if DSV32_OLD not in src:
        return "pattern-not-found"
    if dry_run:
        return "would-patch"
    if not os.path.exists(d + ".orig"):
        shutil.copy(d, d + ".orig")
    tmp = d + ".tmp"
    open(tmp, "w").write(src.replace(DSV32_OLD, DSV32_NEW))
    os.replace(tmp, d)                                   # atomic — a kill mid-write can't corrupt deepseek_v32.py
    return "patched"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--revert", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(PATCH):
        sys.exit(f"  [stop] bundled fix not found: {PATCH}")
    patch_src = open(PATCH).read()
    tg = targets()
    if not tg:
        print("  no mlx_lm installs found (LM Studio not installed, no venv?).")
        return
    changed = 0
    for t in tg:
        tag = "lmstudio" if ".lmstudio" in t else "mlx_lm"
        if args.revert:
            if os.path.exists(t + ".orig"):
                shutil.copy(t + ".orig", t)
                print(f"  [revert {tag}] {t}")
                changed += 1
            else:
                print(f"  [skip {tag}: no .orig] {t}")
            continue
        already = os.path.exists(t) and open(t).read() == patch_src
        if already:
            print(f"  [ok {tag}: already patched] {t}")
            continue
        print(f"  [{'would patch' if args.dry_run else 'PATCH'} {tag}] {t}")
        if args.dry_run:
            continue
        if not os.path.exists(t + ".orig"):           # back up the stub once
            shutil.copy(t, t + ".orig")
        shutil.copy(PATCH, t)
        changed += 1
    # also apply the deepseek_v32.py MoE stop_gradient fix (GRPO/RL portability)
    for t in tg:
        st = patch_dsv32(t, args.dry_run, args.revert)
        if st in ("patched", "reverted", "would-patch"):
            print(f"  [dsv32 {st}] {os.path.join(os.path.dirname(t), 'deepseek_v32.py')}")
            if st in ("patched", "reverted"):
                changed += 1
        elif st == "pattern-not-found":
            print(f"  [dsv32 SKIP: line not found — different mlx_lm version] "
                  f"{os.path.join(os.path.dirname(t), 'deepseek_v32.py')}")
        elif st is None and not args.revert:                 # deepseek_v32.py absent → glm_moe_dsa can't import it
            dsv = os.path.join(os.path.dirname(t), "deepseek_v32.py")
            if not os.path.exists(dsv):
                print(f"  [⚠ dsv32 MISSING — the model WILL fail to load] {dsv}\n"
                      f"      glm_moe_dsa extends deepseek_v32, but your mlx_lm predates DeepSeek-V3.2 support.\n"
                      f"      Fix: pip install -U mlx-lm   (then re-run this patch). Otherwise: ImportError at load.")
    print(f"\n  {'(dry-run) ' if args.dry_run else ''}{changed} file(s) "
          f"{'to change' if args.dry_run else 'changed'}.")
    if changed and not args.dry_run and not args.revert:
        print("  -> FULLY QUIT and reopen LM Studio so it reloads the patched engine.")


if __name__ == "__main__":
    main()
