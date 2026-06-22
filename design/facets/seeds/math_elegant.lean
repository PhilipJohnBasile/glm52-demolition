import Mathlib.Tactic

/- Erdős's "Book": the elegant proof, not the first. The sum of the first n odd numbers is n²
   — proved by induction in two lines, the inductive step closed by `ring` after the right rewrite.
   The structure explains *why*: each step adds the next odd number (2m+1) to m², giving (m+1)². -/
theorem sum_first_odds (n : ℕ) :
    (Finset.range n).sum (fun k => 2 * k + 1) = n ^ 2 := by
  induction n with
  | zero => rfl
  | succ m ih => rw [Finset.sum_range_succ, ih]; ring
