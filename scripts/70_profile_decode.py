#!/usr/bin/env python3
"""Profile the speed root cause: is 3-bit affine dequant the hotspot? Microbenchmark
mx.quantized_matmul at 3-bit vs 4-bit (group 64) on an EXPERT-sized matrix — directly measures
the dequant-on-fetch overhead the research blames (MLX #3402). No 99 GB load. If 4-bit is clearly
faster per matmul, the 4-bit re-quant is confirmed as the fix (not MTP, not active-experts).

  python scripts/70_profile_decode.py
"""
import time

import mlx.core as mx

# GLM-5.2 expert shape (approx): hidden 5120, moe intermediate ~1536 per expert
HIDDEN, INTER = 5120, 1536
N_ACTIVE, MATMULS_PER_EXPERT, LAYERS = 8, 3, 78   # 8 experts/token, gate+up+down, 78 layers


def bench(bits, group=64, iters=300):
    w = mx.random.normal((INTER, HIDDEN)).astype(mx.float16)
    x = mx.random.normal((1, HIDDEN)).astype(mx.float16)   # one decode token
    wq, scales, biases = mx.quantize(w, group_size=group, bits=bits)
    mx.eval(wq, scales, biases, x)
    for _ in range(20):                                    # warmup
        mx.eval(mx.quantized_matmul(x, wq, scales, biases, transpose=True, group_size=group, bits=bits))
    t0 = time.time()
    for _ in range(iters):
        mx.eval(mx.quantized_matmul(x, wq, scales, biases, transpose=True, group_size=group, bits=bits))
    return (time.time() - t0) / iters * 1e6                # microseconds per matmul


def main():
    ops = N_ACTIVE * MATMULS_PER_EXPERT * LAYERS           # expert matmuls per decoded token
    print(f"  expert-sized quantized_matmul (the MoE decode hot path) — {ops} per token:")
    res = {}
    for bits in (3, 4):
        us = bench(bits)
        ms = us * ops / 1000
        res[bits] = ms
        print(f"    {bits}-bit affine g64: {us:6.1f} µs/matmul -> ~{ms:6.1f} ms/token (experts) "
              f"-> ~{1000 / ms:5.1f} tok/s ceiling")
    if 3 in res and 4 in res:
        speedup = res[3] / res[4]
        print(f"  >>> 4-bit is {speedup:.2f}x {'FASTER' if speedup > 1.15 else 'similar'} per matmul.")
        print("  >>> 4-bit re-quant CONFIRMED as the fix." if speedup > 1.3 else
              "  >>> dequant gap smaller than expected — profile attention/routing too.")


if __name__ == "__main__":
    main()
