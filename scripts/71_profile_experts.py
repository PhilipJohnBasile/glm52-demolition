#!/usr/bin/env python3
"""Does reducing active experts actually speed up decode? Microbench the batched expert matmul
(the MoE gather hot path) at top-8 / 6 / 4 — if it scales ~linearly, 8->4 ~halves the per-token
read (the real bandwidth lever for our 3-bit decode)."""
import time
import mlx.core as mx

HIDDEN, INTER, LAYERS = 5120, 1536, 78


def bench_topk(topk, bits=3, group=64, iters=80):
    w = mx.random.normal((topk, INTER, HIDDEN)).astype(mx.float16)
    wq, s, b = mx.quantize(w, group_size=group, bits=bits)
    x = mx.random.normal((topk, 1, HIDDEN)).astype(mx.float16)   # one token per active expert
    mx.eval(wq, s, b, x)
    for _ in range(10):
        mx.eval(mx.quantized_matmul(x, wq, s, b, transpose=True, group_size=group, bits=bits))
    t0 = time.time()
    for _ in range(iters):
        mx.eval(mx.quantized_matmul(x, wq, s, b, transpose=True, group_size=group, bits=bits))
    return (time.time() - t0) / iters * 1e6


print("  per-token expert cost vs active-expert count (3-bit, decode):")
base = None
for topk in (8, 6, 4):
    us = bench_topk(topk)
    ms = us * 3 * LAYERS / 1000          # ~3 matmuls/expert (gate,up,down) x layers
    if base is None:
        base = ms
    print(f"    top-{topk}: ~{ms:6.1f} ms/token (experts)  ->  {base/ms:.2f}x faster vs top-8")
print("  (linear scaling = active-expert reduction is the real, measured lever)")
