#!/usr/bin/env python3
"""#53 Demolition family — shrunken sizes that KEEP all the elite training (design-soul + 7 facets + heals).

The elite training lives in the heal corpus + the facet-inclusive calibration (both SIZE-AGNOSTIC), so every
size stays elite. Per-size pipeline (reuses existing scripts):
  1. scripts/78_facet_calib.py        → calib/facet_mix.jsonl   (exercises all 7 facets → REAP keeps them)
  2. scripts/23_stream_calibrate.py   → expert saliency on the facet mix (router_weight × act_norm, streamed)
  3. scripts/24_apply_prune.py        → prune 77 → <experts>     (facet-safe: niche experts survive)
  4. scripts/04_quantize.py           → quantize to <bits>       (mixed: experts <bits>, attn/embed +1)
  5. scripts/06_heal_lora.py          → SFT on the SAME soul corpus (heal/<facet>/soul.jsonl + seeds + data-v4)
Each → models/GLM-5.2-q<bits>-<name> + a Demolition-<name> HF repo. GPU, multi-pass, hours each.

Size = ~10.4GB FIXED base (embed+lm_head+attention, MEASURED from v4) + experts × ~1.24GB × (bits/3).
The base dominates small models, so <~13GB is impossible — the "floor" experiment is ~14GB, not 7GB.

  python scripts/79_demolition_family.py --plan          # CPU: the family + per-size pipeline
  python scripts/79_demolition_family.py --build 64gb    # GPU: build one
  python scripts/79_demolition_family.py --all           # GPU: queue + build all (largest→smallest)
"""
import argparse
import os
import shutil
import sys

# name,  experts, bits,  ~GB, target hardware,            note   (~GB MEASURED: 10.4GB fixed base + experts×1.24GB×bits/3)
FAMILY = [
    ("67gb", 46, "3",   67, "96 GB Macs",                "drop ~31 lowest-saliency experts"),
    ("55gb", 36, "3",   55, "64 GB Macs",                "half the experts, same training"),
    ("36gb", 26, "2.5", 36, "48 GB Macs",                "fewer experts + 2.5-bit"),
    ("20gb", 16, "2",   20, "32 GB Macs",                "EXPERIMENT — aggressive, expect some loss"),
    ("14gb",  8, "2",   14, "24 GB Mac / 16 GB tight",   "EXPERIMENT — the FLOOR (10.4GB base dominates; <~13GB impossible)"),
]
HERE = os.path.dirname(__file__)


def plan():
    print("  Demolition family — every size keeps the elite training (design-soul + 7 facets):")
    print(f"    {'name':6s} {'experts':>7s} {'bits':>5s} {'~GB':>5s}  hardware")
    for name, experts, bits, gb, hw, note in FAMILY:
        tag = "  ⚗️ " + note if "EXPERIMENT" in note else ""
        print(f"    {name:6s} {experts:>7d} {bits:>5s} {gb:>5d}  {hw}{tag}")
    calib = os.path.join(HERE, "..", "calib", "facet_mix.jsonl")
    print(f"  facet-inclusive calibration ready: {os.path.exists(calib)} ({calib})")
    print("  per-size: facet-calib → saliency → prune → quantize → heal(soul corpus). The calib + heal are")
    print("  size-agnostic, so 64/48/28 stay strong and 14/7 are the aggressive experiments you asked for.")


def build_one(name, experts, bits):
    import subprocess  # noqa: F401  (used when the GPU steps below are uncommented)
    base = os.path.join(HERE, "..")
    src = os.path.join(base, "models", "GLM-5.2-mxfp4")          # 256-expert source for the facet-calibrated re-prune
    sal = os.path.join(base, "models", f"saliency-{name}.npz")
    pruned = os.path.join(base, "models", f"GLM-5.2-pruned-{name}")
    out = os.path.join(base, "models", f"GLM-5.2-q{bits.replace('.', '')}-{name}")
    ratio = round(1 - experts / 256, 4)                         # 24_apply_prune --ratio = fraction to REMOVE (keep=256*(1-ratio))
    be = int(float(bits)); br = be + 1                          # expert bits; rest +1 (q{be}a{br}) — tune per size
    print(f"  building {name}: keep {experts}/256 experts (--ratio {ratio}) @ {bits}-bit → {out}", flush=True)
    q04 = [sys.executable, os.path.join(HERE, "04_quantize.py"), "--src", pruned, "--dst", out]
    if bits == "2.5":                                           # 2.5 is NOT a flat width — int(2.5)=2 would silently == the 2-bit size
        plan = os.path.join(base, "models", f"plan-{name}.json")
        q04 += ["--plan", plan]                                 # build first: src/dynamic_bits.layer_plan(load(sal), 2.5) → plan-<name>.json
        print("    ⚠ 2.5-bit → dynamic_bits.layer_plan(saliency, 2.5) → 04 --plan (half 2-bit / half 3-bit), not a flat 2-bit", flush=True)
    else:
        q04 += ["--bits-experts", str(be), "--bits-rest", str(br)]
    steps = [
        [sys.executable, os.path.join(HERE, "78_facet_calib.py")],
        [sys.executable, os.path.join(HERE, "23_stream_calibrate.py"), "--model", src, "--data", "calib/facet_mix.jsonl", "--out", sal],
        [sys.executable, os.path.join(HERE, "24_apply_prune.py"), "--model", src, "--saliency", sal, "--ratio", str(ratio), "--out", pruned],
        q04,
        [sys.executable, os.path.join(HERE, "06_heal_lora.py"), "--model", out, "--data", "heal/soul", "--skip-data", "--adapter-path", out + "-heal"],
    ]
    for cmd in steps:
        print(f"    $ {' '.join(os.path.basename(c) if c.endswith('.py') else c for c in cmd)}", flush=True)
        # subprocess.run(cmd, cwd=base, check=True)   # uncomment to execute on the GPU
    # DUAL-FORMAT: also emit GGUF from the pruned BF16 (branch before the MLX quant) → llama.cpp/Ollama/LM Studio.
    # Small soul-trained demolition models in GGUF — a value-add nobody else has. (Runs full-attn until llama.cpp
    # adds the DSA indexer; the GLM-MoE-DSA arch is already merged, PR #19460.) GGUF is CONDITIONAL on llama.cpp —
    # the MLX model is complete without it, so a missing toolchain must NOT fail the family build.
    if shutil.which("llama-quantize"):                          # llama.cpp present; convert_hf_to_gguf.py ships in its source tree (set LLAMA_CPP_DIR), not on PATH
        print(f"    $ convert_hf_to_gguf.py {out}-bf16 --outfile {out}.gguf   # llama.cpp")
        print(f"    $ llama-quantize {out}.gguf {out}-Q4_K_M.gguf Q4_K_M")
        print(f"    → MLX {out}  +  GGUF {out}-Q4_K_M.gguf  → eval (80) + hf upload Demolition-{name} (MLX & GGUF)")
    else:
        print(f"    → MLX {out}  → eval (80) + hf upload Demolition-{name} (MLX). "
              f"GGUF SKIPPED — install llama.cpp (`brew install llama.cpp`) to also emit the GGUF; MLX is complete without it.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--build", default="")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if a.build:
        name, experts, bits = next((n, e, b) for n, e, b, *_ in FAMILY if n == a.build)
        build_one(name, experts, bits)
    elif a.all:
        for name, experts, bits, *_ in FAMILY:               # largest → smallest
            build_one(name, experts, bits)
    else:
        plan()


if __name__ == "__main__":
    main()
