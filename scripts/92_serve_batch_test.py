#!/usr/bin/env python3
"""Verify the SERVE delivers batching throughput (#71). mlx_lm.server batches concurrent requests when
is_batchable (no draft model = us). Fire B requests CONCURRENTLY vs SEQUENTIALLY, compare total tok/s.
The standalone probe (91) showed the model scales 2.6x at B=8; this proves the live serve realises it.
  # serve must be up on :8080 first
  python scripts/92_serve_batch_test.py --b 6
"""
import argparse
import concurrent.futures as cf
import json
import time
import urllib.request

URL = "http://127.0.0.1:8080/v1/chat/completions"
PROMPT = ("Write a Python function that merges two sorted lists into one sorted list, "
          "with a docstring and type hints.")


def one(_=None):
    body = json.dumps({"messages": [{"role": "user", "content": PROMPT}], "max_tokens": 80,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=600).read())
    return d["usage"]["completion_tokens"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b", type=int, default=6)
    B = ap.parse_args().b
    one()                                                    # warm one request (prompt-cache the system prefix)
    t0 = time.time()                                          # CONCURRENT: B requests in flight at once → serve batches them
    with cf.ThreadPoolExecutor(B) as ex:
        ctoks = list(ex.map(one, range(B)))
    ct = time.time() - t0
    t0 = time.time()                                          # SEQUENTIAL: one at a time → no batching
    stoks = [one() for _ in range(B)]
    st = time.time() - t0
    cps, sps = sum(ctoks) / ct, sum(stoks) / st
    print(f"\n  concurrent B={B}: {sum(ctoks)} tok in {ct:5.1f}s = {cps:5.1f} tok/s")
    print(f"  sequential B={B}: {sum(stoks)} tok in {st:5.1f}s = {sps:5.1f} tok/s")
    print(f"  → SERVE batching speedup = {cps / sps:.2f}x  ({'✓ batches' if cps / sps > 1.4 else '✗ not batching — check is_batchable'})")


if __name__ == "__main__":
    main()
