#!/usr/bin/env python3
"""Batch-scaling probe (#71) — does batching amortize the MoE expert-load? The decisive measurement.

On a memory-bound MoE, batching B sequences loads the UNION of their active experts (~B×8, saturating at the
77 kept experts) while processing B tokens per forward. So total throughput scales with B *only once the union
saturates* — below that, each added sequence loads ~its own new experts (no amortization). This measures REAL
total tok/s at B = 1/2/4/8 to see where (if anywhere) the curve bends up. Verify-before-claim: I asserted
"batching is the real speed"; this proves whether it actually scales on THIS demolished MoE.
  python scripts/91_batch_scaling.py
"""
import os
import sys
import time

os.environ.setdefault("GLM_STREAM_EVAL", "0")            # match the serve; the model fits
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import mlx.core as mx
import mlx_lm
from mlx_lm.models import cache as C

MODEL = os.path.join(os.path.dirname(__file__), "..", "models", "GLM-5.2-q3a4-v4")


def main():
    print(f"  loading {os.path.basename(MODEL)} …", flush=True)
    model, tok = mlx_lm.load(MODEL)
    ids = tok.encode("Write a Python function that merges two sorted lists into one sorted list, "
                     "with a docstring and type hints, then explain its time complexity.")
    N = 48
    print(f"  prompt {len(ids)} tok · generating {N}/seq · GLM_STREAM_EVAL={os.environ['GLM_STREAM_EVAL']}\n", flush=True)
    base = None
    for B in (1, 2, 4, 8):
        try:
            kv = C.make_prompt_cache(model)
            x = mx.repeat(mx.array(ids)[None], B, axis=0)            # [B, T] — B copies of the prompt
            model(x[:, :-1], cache=kv)                               # prefill all B
            mx.eval([c.state for c in kv])
            y = x[:, -1:]
            t0 = time.time()
            for _ in range(N):
                y = mx.argmax(model(y, cache=kv)[:, -1:], axis=-1)   # one batched forward → B next tokens
                mx.eval(y)
            dt = time.time() - t0
            total = B * N / dt
            base = base or total
            print(f"  B={B:2d}: {B * N:3d} tok in {dt:5.1f}s = {total:5.1f} tok/s total "
                  f"({total / B:4.1f}/seq) — {total / base:.2f}x vs B=1", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"  B={B:2d}: FAILED — {str(e)[:120]}", flush=True)
            break
    print("\n  → total tok/s SCALES with B  ⇒ batching is the real throughput win (the speed pillar).")
    print("    total tok/s ~FLAT          ⇒ even batching can't amortize this MoE → speed is truly maxed.")


if __name__ == "__main__":
    main()
