"""Prefix-aware prompt caching — the #1 speed win for AGENTIC use (research 2026-06-17).

A coding agent sends dozens of calls whose prompt is mostly the SAME growing prefix (system prompt +
history + tool results) with a little new text each step. `mlx_lm.server` drops the KV cache whenever
the prefix shifts, so every step re-prefills the *entire* context — 30-90 s/step, ~200 s on a 40K ctx.
Reusing the cache for the common prefix and prefilling only the new suffix cuts time-to-first-token by
up to ~9.7x — the difference between "usable" and "unusable" local agents.

We can't rely on a drop-in engine (Rapid-MLX/oMLX/MetalRT don't support our `glm_moe_dsa` arch — checked),
so we manage the cache ourselves with mlx-lm's primitives: ONE persistent cache across steps, reused up
to the point the new prompt diverges, then prefill only the suffix.

The prefix-planning logic (the novel, important part) is pure and unit-tested below — GPU-free. The
actual generation needs the model loaded; `generate()` is wired to the mlx-lm API and gets its real
TTFT numbers measured on the served model once the GPU is free (see `selftest` vs `measure`).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


def common_prefix_len(a: list[int], b: list[int]) -> int:
    """Number of leading token-ids shared by two sequences — how much KV cache can be reused."""
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


@dataclass
class CachePlan:
    reuse: int      # tokens kept from the existing cache (the shared prefix)
    trim: int       # tokens to drop from the END of the cache (cached past the divergence point)
    suffix: list[int]  # the new tokens to actually prefill
    total: int      # full prompt length (for the hit-rate stat)

    @property
    def hit_rate(self) -> float:
        return self.reuse / self.total if self.total else 0.0


@dataclass
class PromptCacheSession:
    """Holds a model + ONE persistent KV cache across agent steps; reuses the common prefix."""
    model: object = None
    tokenizer: object = None
    _cache: object = None
    _cached_ids: list[int] = field(default_factory=list)
    stats: dict = field(default_factory=lambda: {"calls": 0, "prefilled": 0, "reused": 0})

    # ----- GPU-free: the planning logic (unit-tested) -----
    def plan(self, new_ids: list[int]) -> CachePlan:
        """Given the next prompt's token-ids, decide how much cache to reuse vs re-prefill.
        Reuse the shared leading prefix; drop any cached tokens past the divergence; prefill the rest."""
        reuse = common_prefix_len(self._cached_ids, new_ids)
        trim = len(self._cached_ids) - reuse
        return CachePlan(reuse=reuse, trim=trim, suffix=new_ids[reuse:], total=len(new_ids))

    # ----- needs the model (GPU): real generation, measured live -----
    def _ensure_cache(self):
        if self._cache is None:
            from mlx_lm.models.cache import make_prompt_cache
            self._cache = make_prompt_cache(self.model)
            self._cached_ids = []

    def generate(self, prompt: str, max_tokens: int = 512, **kw):
        """Generate reusing the cached prefix; only the new suffix is prefilled. Returns (text, info)."""
        from mlx_lm import stream_generate
        from mlx_lm.models.cache import trim_prompt_cache

        self._ensure_cache()
        new_ids = self.tokenizer.encode(prompt)
        p = self.plan(new_ids)
        if p.trim > 0:                                   # diverged before the cached end → roll back
            trim_prompt_cache(self._cache, p.trim)
            self._cached_ids = self._cached_ids[:p.reuse]

        feed = p.suffix if p.suffix else new_ids[-1:]    # never feed empty
        t0 = time.time()
        ttft = None
        text, gen_ids = [], []
        for resp in stream_generate(self.model, self.tokenizer, feed,
                                    max_tokens=max_tokens, prompt_cache=self._cache, **kw):
            if ttft is None:
                ttft = time.time() - t0                  # first token = the prefill cost we cut
            text.append(resp.text)
            if getattr(resp, "token", None) is not None:
                gen_ids.append(resp.token)

        self._cached_ids = new_ids + gen_ids             # cache now holds prompt + what we generated
        self.stats["calls"] += 1
        self.stats["prefilled"] += len(p.suffix)
        self.stats["reused"] += p.reuse
        return "".join(text), {"ttft_s": ttft, "reused": p.reuse, "prefilled": len(p.suffix),
                               "hit_rate": round(p.hit_rate, 3)}

    # ----- SSD persistence: warm-start across sessions (#85) -----
    def save(self, path: str) -> str:
        """Persist the KV cache + cached token-ids to the SSD (14.5 GB/s) so the NEXT session
        warm-starts this exact context with a disk-load instead of a full re-prefill."""
        import json
        import os
        from mlx_lm.models.cache import save_prompt_cache
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        save_prompt_cache(path, self._cache, metadata={"cached_ids": json.dumps(self._cached_ids)})
        return path

    def load(self, path: str) -> bool:
        """Restore a persisted KV cache from the SSD. Returns True if a warm cache was loaded
        (so the agent skips re-prefilling the system prompt + repo context it saw last session)."""
        import json
        import os
        from mlx_lm.models.cache import load_prompt_cache
        if not os.path.exists(path):
            return False
        self._cache, meta = load_prompt_cache(path, return_metadata=True)
        self._cached_ids = json.loads(meta.get("cached_ids", "[]"))
        return True


def cache_path(key: str, root: str | None = None) -> str:
    """Stable SSD path for a (repo + system-prompt) key — the warm-start file for that context.
    Same repo + same system prompt next session -> same file -> instant warm start."""
    import hashlib
    import os
    root = root or os.path.expanduser("~/.cache/glm_prompt_cache")
    return os.path.join(root, hashlib.sha256(key.encode()).hexdigest()[:16] + ".safetensors")


def _selftest():
    """GPU-free: prove the prefix-planning is correct (the part that delivers the win)."""
    assert common_prefix_len([1, 2, 3], [1, 2, 9]) == 2
    assert common_prefix_len([], [1]) == 0
    assert common_prefix_len([1, 2], [1, 2]) == 2

    s = PromptCacheSession()
    # step 1: cold — nothing cached, prefill everything
    p = s.plan([10, 11, 12])
    assert (p.reuse, p.trim, p.suffix) == (0, 0, [10, 11, 12]), p
    s._cached_ids = [10, 11, 12, 99]                      # pretend we generated token 99

    # step 2: agent appended (same prefix + new tokens) — reuse 4, prefill only the 2 new
    p = s.plan([10, 11, 12, 99, 20, 21])
    assert (p.reuse, p.trim, p.suffix) == (4, 0, [20, 21]), p
    assert p.hit_rate == 4 / 6

    # step 3: prefix shifted at pos 2 (e.g. context edited) — reuse 2, trim the 2 stale, prefill the rest
    p = s.plan([10, 11, 77, 78])
    assert (p.reuse, p.trim, p.suffix) == (2, 2, [77, 78]), p

    # SSD persistence round-trip (#85) — GPU-free: dummy KV cache -> save -> load -> verify
    import mlx.core as mx
    from mlx_lm.models.cache import KVCache, load_prompt_cache, save_prompt_cache
    cache = [KVCache()]
    cache[0].update_and_fetch(mx.random.normal((1, 2, 5, 8)), mx.random.normal((1, 2, 5, 8)))
    mx.eval(cache[0].keys, cache[0].values)
    import os as _os
    import tempfile
    fp = _os.path.join(tempfile.gettempdir(), "pc_ssd_test.safetensors")
    save_prompt_cache(fp, cache, metadata={"cached_ids": "[1, 2, 3]"})
    c2, meta = load_prompt_cache(fp, return_metadata=True)
    off = cache[0].offset
    assert mx.allclose(cache[0].keys[..., :off, :], c2[0].keys[..., :off, :]), "KV mismatch after round-trip"
    assert meta["cached_ids"] == "[1, 2, 3]", meta
    _os.remove(fp)
    print("  SSD persistence PASS — KV cache survives save->load with metadata intact (#85)")

    print("  prompt_cache selftest PASS — prefix-diff + trim logic correct (GPU-free)")
    print("  reuse/prefill planning verified; live TTFT measure pending GPU (use `measure` on the server)")


if __name__ == "__main__":
    _selftest()
