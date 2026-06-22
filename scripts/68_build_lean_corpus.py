#!/usr/bin/env python3
"""Build the LEAN heal source — formal proofs as training data, so the model learns to WRITE Lean
4 tactics (the skill it's never seen). A curated seed of basic theorem->proof pairs now (GPU-free,
low memory); --download pulls the real scale (Lean Workbook / mathlib extractions, the data
DeepSeek-Prover & Goedel train on) — DEFER that until the GPU/proof is free (it's network+memory
heavy and can OOM-crash a running server). Output: heal/lean/train.jsonl (a `math`-domain source).

  python scripts/68_build_lean_corpus.py             # curated seed (safe anytime)
  python scripts/68_build_lean_corpus.py --download   # + Lean Workbook (run only when GPU is free)
"""
import argparse
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "heal", "lean")

# (informal statement, Lean 4 proof) — teaches tactic syntax. Real, checkable, expandable.
SEED = [
    ("Prove that 2 + 2 = 4.", "theorem two_add_two : 2 + 2 = 4 := by rfl"),
    ("Prove that for any natural n, n + 0 = n.", "theorem add_zero' (n : Nat) : n + 0 = n := by rfl"),
    ("Prove that addition of naturals is commutative.",
     "theorem add_comm' (a b : Nat) : a + b = b + a := by exact Nat.add_comm a b"),
    ("Prove that for reals, (a + b)^2 = a^2 + 2*a*b + b^2.",
     "theorem sq_add (a b : Real) : (a + b)^2 = a^2 + 2*a*b + b^2 := by ring"),
    ("Prove that if a = b and b = c then a = c.",
     "theorem trans' {a b c : Nat} (h1 : a = b) (h2 : b = c) : a = c := by rw [h1, h2]"),
    ("Prove that for any proposition p, p → p.",
     "theorem id_imp (p : Prop) : p → p := fun h => h"),
    ("Prove that p ∧ q implies q ∧ p.",
     "theorem and_swap (p q : Prop) (h : p ∧ q) : q ∧ p := ⟨h.2, h.1⟩"),
    ("Prove that the sum of the first n naturals is n*(n+1)/2 (by induction).",
     "theorem sum_n (n : Nat) : 2 * (Finset.range (n+1)).sum id = n * (n + 1) := by\n"
     "  induction n with\n  | zero => rfl\n  | succ k ih => simp [Finset.sum_range_succ]; omega"),
    ("Prove that for naturals, a * (b + c) = a * b + a * c.",
     "theorem mul_add' (a b c : Nat) : a * (b + c) = a * b + a * c := by exact Nat.mul_add a b c"),
    ("Prove that 0 ≤ n for any natural n.",
     "theorem zero_le' (n : Nat) : 0 ≤ n := by exact Nat.zero_le n"),
    ("Prove that if n is even then n^2 is even.",
     "theorem even_sq {n : Nat} (h : Even n) : Even (n^2) := by\n"
     "  obtain ⟨k, hk⟩ := h; exact ⟨2*k^2, by rw [hk]; ring⟩"),
    ("Prove p ∨ q implies q ∨ p.",
     "theorem or_swap (p q : Prop) (h : p ∨ q) : q ∨ p := by\n"
     "  rcases h with hp | hq\n  · exact Or.inr hp\n  · exact Or.inl hq"),
]


def build(download):
    rows = [{"messages": [{"role": "user", "content": "Prove in Lean 4. Output only the theorem and "
                           "proof.\n" + s}, {"role": "assistant", "content": p}]} for s, p in SEED]
    if download:
        try:
            from datasets import load_dataset
            ds = load_dataset("internlm/Lean-Workbook", split="train", streaming=True)
            for i, ex in enumerate(ds):
                stmt = ex.get("natural_language_statement") or ex.get("problem") or ""
                proof = ex.get("formal_proof") or ex.get("proof") or ex.get("formal_statement") or ""
                if stmt and proof:
                    rows.append({"messages": [{"role": "user", "content": "Prove in Lean 4.\n" + stmt},
                                              {"role": "assistant", "content": proof}]})
                if len(rows) >= 4000:
                    break
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ Lean-Workbook download failed ({str(e)[:80]}) — seed only; try another source.")
    os.makedirs(OUT, exist_ok=True)
    nv = max(2, len(rows) // 20)
    open(os.path.join(OUT, "valid.jsonl"), "w").write("\n".join(json.dumps(r) for r in rows[:nv]))
    open(os.path.join(OUT, "train.jsonl"), "w").write("\n".join(json.dumps(r) for r in rows[nv:]))
    print(f"  lean corpus -> {OUT}: {len(rows)} rows ({len(SEED)} curated seed"
          f"{' + downloaded' if download else '; run --download for scale when GPU is free'})")
    return len(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true")
    build(ap.parse_args().download)
