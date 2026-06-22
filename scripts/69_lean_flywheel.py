#!/usr/bin/env python3
"""Lean flywheel (#46 + #28) — AUTONOMOUS multi-round expert iteration. Each round:
  serve (MLX-bounded) → eval pass@1 → gen (prove + self-correction trajectories + scaffold failures)
  → SFT a new adapter on the accumulated verified proofs → repeat.
pass@1 should CLIMB then saturate (the self-improving curve). Fully local, MLX-bounded, crash-resilient.

  python scripts/69_lean_flywheel.py --rounds 3

This is the orchestrator; it shells the pieces we built (serve_stable, 67 gen+scaffold, 06_heal_lora,
66_prove) with timeouts + cleanup. GPU-free to import/compile; runs on the GPU for real rounds.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from stability import run_with_lifecycle  # noqa: E402  (subprocess timeout + group-kill, no zombies)

PY = ".venv/bin/python"
MODEL = "models/GLM-5.2-q3a4-v4"
URL = "http://127.0.0.1:8080/v1"


def kill_server():
    subprocess.run("pkill -f 'serve_stable|mlx_lm.server'", shell=True, cwd=ROOT)
    time.sleep(4)


def serve(adapter):
    kill_server()
    subprocess.Popen(
        f"GLM_STREAM_EVAL=1 MLX_MEM_GB=118 {PY} scripts/serve_stable.py --model {MODEL} "
        f"--adapter-path {adapter} --port 8080 > logs/serve_fly.log 2>&1",
        shell=True, cwd=ROOT, start_new_session=True)
    for _ in range(75):
        try:
            urllib.request.urlopen(URL + "/models", timeout=5)
            return True
        except Exception:  # noqa: BLE001
            time.sleep(8)
    return False


def pass_at_1():
    _, out = run_with_lifecycle(
        f'export PATH="$HOME/.elan/bin:$PATH"; {PY} scripts/66_prove.py --n 5 --attempts 1 --correct 0 '
        f"--base-url {URL} --model {MODEL}", cwd=ROOT, timeout=600)
    m = re.search(r"FORMAL-MATH:\s*(\d+)/(\d+)", out)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 5)


def gen():
    # conjecturer self-play (plateau lever #1): propose NOVEL theorems → curriculum.jsonl, fresh each round
    run_with_lifecycle(
        f'export PATH="$HOME/.elan/bin:$PATH"; {PY} scripts/67_lean_expert.py conjecture --base-url {URL} '
        f"--model {MODEL}", cwd=ROOT, timeout=600)
    # prover: prove THEOREMS + the conjectured/scaffold curriculum, save self-correction trajectories
    run_with_lifecycle(
        f'export PATH="$HOME/.elan/bin:$PATH"; {PY} scripts/67_lean_expert.py gen --base-url {URL} '
        f"--model {MODEL} --attempts 3 --correct 2", cwd=ROOT, timeout=2700)


def _merge_jsonl(srcs, dst):
    """Safe JSONL merge: validate each line + write proper newlines. `cat a b` corrupts the boundary when
    `a` lacks a trailing newline (merges a's last line into b's first) → mlx_lm JSONDecodeError. THE bug that
    silently broke flywheel compounding. Returns rows written."""
    n = 0
    with open(dst, "w") as out:
        for src in srcs:
            if not os.path.exists(src):
                continue
            for line in open(src):
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                out.write(line + "\n")
                n += 1
    return n


def sft(new_adapter):
    # combine the Lean corpus + the model's own verified proofs/trajectories (anti-forgetting), SAFELY
    os.makedirs(os.path.join(ROOT, "heal", "lean-fly"), exist_ok=True)
    nt = _merge_jsonl([os.path.join(ROOT, "heal", "lean", "train.jsonl"),
                       os.path.join(ROOT, "heal", "lean-rft", "train.jsonl")],
                      os.path.join(ROOT, "heal", "lean-fly", "train.jsonl"))
    _merge_jsonl([os.path.join(ROOT, "heal", "lean", "valid.jsonl")],
                 os.path.join(ROOT, "heal", "lean-fly", "valid.jsonl"))
    print(f"  sft: merged {nt} validated train rows -> heal/lean-fly", flush=True)
    run_with_lifecycle(
        f"GLM_STREAM_EVAL=0 {PY} scripts/06_heal_lora.py --model {MODEL} --mode sft --skip-data "
        f"--data heal/lean-fly --adapter-path {new_adapter} --no-mask-prompt --num-layers 6 "
        f"--iters 250 --max-seq-length 1024", cwd=ROOT, timeout=2700)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--start-adapter", default="heal/adapters-lean")
    args = ap.parse_args()

    adapter, history = args.start_adapter, []
    for rnd in range(1, args.rounds + 1):
        print(f"\n=== FLYWHEEL ROUND {rnd} (adapter: {adapter}) ===", flush=True)
        if not serve(adapter):
            print("  serve failed — stopping")
            break
        p, n = pass_at_1()
        history.append(p)
        print(f"  round {rnd} pass@1: {p}/{n}", flush=True)
        gen()                                  # prove + self-correction trajectories + scaffold failures→curriculum
        kill_server()
        new_adapter = f"heal/adapters-lean-r{rnd}"
        sft(new_adapter)                       # SFT on its own verified proofs → compound
        adapter = new_adapter
    kill_server()
    print(f"\n  FLYWHEEL pass@1 across rounds: {history}  (climb→saturate = self-improvement working)")


if __name__ == "__main__":
    main()
