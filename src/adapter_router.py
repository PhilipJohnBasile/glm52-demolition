#!/usr/bin/env python3
"""Adapter router — pick the right specialist LoRA per task (a mixture-of-specialists at serve time).

We healed several adapters; routing a task to the *matching* one beats one-size-fits-all. CPU signal-classifier
here; the actual hot-swap serve is GPU. Compounds with best-of-N: route → N candidates from the right specialist →
verify → keep the passer. Math/proof → the Lean adapter, design/UI → the design-soul adapter, everything else → the
general v4. Falls back gracefully if a specialist adapter isn't on disk yet.
"""
import os
import re

HERE = os.path.dirname(__file__)
_ROOT = os.path.join(HERE, "..")


def _pick(*cands):
    for c in cands:
        if os.path.isdir(os.path.join(_ROOT, c)):
            return c
    return "heal/adapters-v4"


ADAPTERS = {
    "lean":   _pick("heal/adapters-lean-v2", "heal/adapters-lean"),
    "design": _pick("heal/adapters-design", "heal/adapters-v4"),
    "code":   _pick("heal/adapters-v4", "heal/adapters"),
}
_SIGNALS = {
    "lean":   re.compile(r"(theorem|lemma|\bprove\b|Lean|mathlib|tactic|by_contra|nlinarith|simp\b|∀|∃|⊢|∑|∫|ℕ|ℝ)", re.I),
    "design": re.compile(r"(CSS|OKLCH|WCAG|layout|flexbox|\bgrid\b|\bUI\b|component|responsive|typography|palette|navbar|button|contrast)", re.I),
}


def route(task: str):
    """Return (facet, adapter_path) for the task."""
    t = task or ""
    scores = {k: len(rx.findall(t)) for k, rx in _SIGNALS.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        best = "code"
    return best, ADAPTERS[best]


def _selftest():
    cases = [
        ("Prove that for all n : ℕ, n + 0 = n", "lean"),
        ("by_contra h; nlinarith [sq_nonneg x]", "lean"),
        ("Build a responsive navbar with OKLCH colors on an 8px grid", "design"),
        ("Improve the button component's WCAG contrast ratio", "design"),
        ("Fix the failing test in parser.rs", "code"),
        ("Refactor this function for readability", "code"),
    ]
    for task, expect in cases:
        facet, adapter = route(task)
        assert facet == expect, f"{task[:40]!r} → {facet}, expected {expect}"
        print(f"  OK  {facet:6s} → {adapter:22s} ← {task[:44]}")
    print("  adapter_router selftest PASS — mixture-of-specialists (math→lean, design→design, else→code)")


if __name__ == "__main__":
    _selftest()
