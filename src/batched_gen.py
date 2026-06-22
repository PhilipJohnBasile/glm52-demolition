"""#48 + #35 — batched generation for parallel proof-search / best-of-N (M5 Max throughput). The GPU-free
batching helpers (grouping + left-padding + fanout/demux) are here + unit-tested; the actual batched decode
plugs into mlx_lm.batch_generate (GPU). Running N proof attempts in ONE batched forward is the throughput
win for the flywheel's gen step (vs sequential best-of-N), and the basis for continuous batching.
"""
from __future__ import annotations


def make_batches(items, batch_size):
    """Group items into batches of <= batch_size (the unit of one batched forward)."""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def pad_left(token_lists, pad_id=0):
    """Left-pad token sequences to equal length — left-pad keeps the autoregressive write position aligned at
    the right edge across the batch. Returns (padded, original_lengths)."""
    if not token_lists:
        return [], []
    m = max(len(t) for t in token_lists)
    padded = [[pad_id] * (m - len(t)) + list(t) for t in token_lists]
    return padded, [len(t) for t in token_lists]


def fanout(prompts, n):
    """Best-of-N fanout: each prompt repeated n times so one batched decode yields n candidates each. Returns
    (flat_prompts, owner_index) so results demux back to their originating prompt."""
    flat, owner = [], []
    for i, p in enumerate(prompts):
        for _ in range(n):
            flat.append(p)
            owner.append(i)
    return flat, owner


def demux(results, owner, n_prompts):
    """Inverse of fanout: group flat results back by their originating prompt index."""
    out = [[] for _ in range(n_prompts)]
    for r, o in zip(results, owner):
        out[o].append(r)
    return out


def batched_best_of_n(prompts, n, gen_batch_fn, verify_fn):
    """Generate n candidates per prompt via ONE batched call (gen_batch_fn(flat_prompts) -> list[str]), then
    pick the first verified candidate per prompt. gen_batch_fn is the GPU step (mlx_lm.batch_generate)."""
    flat, owner = fanout(prompts, n)
    grouped = demux(gen_batch_fn(flat), owner, len(prompts))
    return [next((c for c in cands if verify_fn(c)), None) for cands in grouped]


def batched_best_of_n_parallel(prompts, n, gen_batch_fn, verify_fn, workers=None):
    """#82: like batched_best_of_n but the VERIFY fans across the 18 cores (verify_many) — the win when
    verify is compile+run. One batched GPU gen, then ALL n*prompts candidates verified in parallel; the
    first passer per prompt. Turns N serial verifiers into ~one verifier of wall-clock."""
    from verifiers import verify_many
    flat, owner = fanout(prompts, n)
    cands_flat = list(gen_batch_fn(flat))
    oks = verify_many([(c,) for c in cands_flat], fn=verify_fn, workers=workers)
    gc, go = demux(cands_flat, owner, len(prompts)), demux(list(oks), owner, len(prompts))
    return [next((c for c, o in zip(cs, os_) if o), None) for cs, os_ in zip(gc, go)]


def _selftest():
    assert make_batches([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    padded, lens = pad_left([[1, 2], [3]], pad_id=0)
    assert padded == [[1, 2], [0, 3]] and lens == [2, 1], (padded, lens)
    flat, owner = fanout(["a", "b"], 3)
    assert flat == ["a", "a", "a", "b", "b", "b"] and owner == [0, 0, 0, 1, 1, 1]
    assert demux(["x1", "x2", "x3", "y1", "y2", "y3"], owner, 2) == [["x1", "x2", "x3"], ["y1", "y2", "y3"]]
    win = batched_best_of_n(["p", "q"], 2, lambda fl: ["bad", "good", "no", "yes"],
                            lambda c: c in ("good", "yes"))
    assert win == ["good", "yes"], win
    import time
    def _slow(c):
        time.sleep(0.15)
        return c in ("good", "yes")
    t0 = time.time()
    winp = batched_best_of_n_parallel(["p", "q"], 2, lambda fl: ["bad", "good", "no", "yes"], _slow)
    dt = time.time() - t0
    assert winp == ["good", "yes"], winp
    assert dt < 0.5, f"verify not parallel ({dt:.2f}s; serial would be ~0.6s)"
    print(f"  batched_gen selftest PASS (#48/#35/#82): +parallel best-of-N — 4 verifies in {dt:.2f}s (serial ~0.6s)")


if __name__ == "__main__":
    _selftest()
