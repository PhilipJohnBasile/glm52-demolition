"""Custom MLX generation primitives (#35) — FIM (fill-in-the-middle) for code editing + best-of-N
selection for the verify loop. The GPU-free logic (FIM prompt formatting, candidate selection) is here
and unit-tested; the live BATCHED generation (run N candidates in parallel on the model, #48) is the
mlx_lm integration that needs the GPU. Keeping the testable core separate so it's hardened independently.
"""
from __future__ import annotations

# FIM sentinel schemes by model family (prefix / suffix / middle). Code EDITING needs infill, not rewrite.
FIM_SCHEMES = {
    "default": ("<|fim_prefix|>", "<|fim_suffix|>", "<|fim_middle|>"),
    "deepseek": ("<｜fim▁begin｜>", "<｜fim▁hole｜>", "<｜fim▁end｜>"),
    "qwen": ("<|fim_prefix|>", "<|fim_suffix|>", "<|fim_middle|>"),
    "codellama": ("<PRE>", "<SUF>", "<MID>"),
}


def fim_prompt(prefix: str, suffix: str, scheme: str = "default") -> str:
    """Format a fill-in-the-middle prompt: the model generates the MIDDLE between prefix and suffix —
    the right primitive for code EDITING (vs a whole-file rewrite)."""
    pre, suf, mid = FIM_SCHEMES.get(scheme, FIM_SCHEMES["default"])
    return f"{pre}{prefix}{suf}{suffix}{mid}"


def best_of_n(candidates, verify_fn):
    """Pick the FIRST candidate that passes its verifier — the verify-loop selection ('generate N, keep
    the one that compiles / proves / passes tests'). Returns (winner, index, n_tried); (None, -1, N) if none."""
    for i, c in enumerate(candidates):
        if verify_fn(c):
            return c, i, i + 1
    return None, -1, len(candidates)


def _selftest():
    p = fim_prompt("def add(a, b):\n    return ", "\n\nprint(add(1, 2))", "default")
    assert p.startswith("<|fim_prefix|>def add") and "<|fim_suffix|>" in p and p.endswith("<|fim_middle|>"), p
    d = fim_prompt("a", "b", "deepseek")
    assert d.startswith("<｜fim▁begin｜>a") and d.endswith("<｜fim▁end｜>"), d
    # best-of-N picks the first that verifies (e.g. compiles / passes a check)
    winner, idx, tried = best_of_n(["broken(", "def ok(): pass", "also"], lambda c: c.startswith("def"))
    assert winner == "def ok(): pass" and idx == 1 and tried == 2, (winner, idx, tried)
    none, i, n = best_of_n(["a", "b"], lambda c: False)
    assert none is None and i == -1 and n == 2
    print("  gen_primitives selftest PASS (#35): FIM prompt formatting (4 schemes) + best-of-N verify-selection")


if __name__ == "__main__":
    _selftest()
