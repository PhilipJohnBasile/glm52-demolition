# Elite Mathematics & Proof: Gold Standard for SFT Healing

> **Purpose.** This document is the research foundation for generating SFT gold data that heals a
> competent-but-not-elite model into one that *proves like the masters*. Every section maps
> directly to training-data construction: the canon names the style targets; the criteria drive
> the audit gate; the gold examples *are* training examples (or seeds for generation); the audit
> pseudocode is the filter applied before any example enters the corpus.

---

## 1. THE ELITE CANON

Ordered roughly chronologically. Each entry names the mathematician, their signature on
*mathematical elegance*, and the concrete lesson for SFT data.

---

### 1.1 Euclid of Alexandria (~300 BC)
**Signature:** Axiomatic economy. Start from the minimal set of assumptions; build each result
on the last with no hidden imports. His proof of infinite primes (Elements IX.20) is the
archetype of "Book proof": assume finiteness, construct a contradiction in three lines.

**Lesson for SFT:** Every proof should name its assumptions explicitly and never sneak in a
lemma without citing it.

---

### 1.2 Leonhard Euler (1707–1783)
**Signature:** Audacious generalization + notational invention. Euler would write the formula
first, verify it on many cases, then supply the proof—a heuristic style that still influenced
every analytic number theorist after him. His solution to the Basel problem (∑ 1/n² = π²/6)
was *technically* incomplete but revealed the right answer and the right structure.

**Lesson for SFT:** Motivate before you prove. Show why you expect the answer before deriving
it. Euler-style computation steps should be narrated, not dropped silently.

---

### 1.3 Carl Friedrich Gauss (1777–1855)
**Signature:** Perfection before publication + seeking multiple independent proofs of the same
result. Gauss found 8 proofs of quadratic reciprocity precisely *because* each proof illuminates
a different facet of why the theorem is true. His Disquisitiones Arithmeticae sets the standard
for structured, layered exposition.

**Lesson for SFT:** "The first proof" and "the best proof" are different. A gold example should
be *the* proof that explains, not the historically first one that merely verifies.

---

### 1.4 Augustin-Louis Cauchy (1789–1857)
**Signature:** Forward-backward induction (Cauchy induction)—a proof technique he invented to
establish AM-GM. Rather than inducting step-by-step, prove for powers of 2 (forward) then
descend to all integers (backward). This is elegant because it avoids case-by-case drudgery
by choosing the *right* induction scheme.

**Lesson for SFT:** Choose the induction principle that fits the problem's symmetry. Wrong
induction = ugly proof.

---

### 1.5 Georg Cantor (1845–1918)
**Signature:** Diagonal arguments and cardinality. The 1891 diagonal argument for uncountability
of ℝ is 4 pages, needs no analysis, and permanently changed what "size of a set" means.

**Lesson for SFT:** The most powerful proofs sometimes introduce a single new *operation* (here:
diagonalize) rather than a chain of algebraic manipulations. A good SFT example should highlight
the key construction explicitly.

---

### 1.6 G.H. Hardy (1877–1947)
**Signature:** Beauty as criterion + the apology framework. Hardy's three criteria for a
beautiful proof: *unexpectedness* (the conclusion should not be where you thought you were
going), *inevitability* (once you see it, it could not have been otherwise), *economy*
(no line wasted). From *A Mathematician's Apology* (1940): "Beauty is the first test; there
is no permanent place in the world for ugly mathematics."

**Lesson for SFT:** Audit unexpectedness and economy. A proof that plods to an obvious
conclusion, or one that has redundant lemmas, fails Hardy's test even if correct.

---

### 1.7 Srinivasa Ramanujan (1887–1920)
**Signature:** Intuition-first, proof-second (or never). Ramanujan's notebooks contain
thousands of identities he stated without proof; Hardy had to supply the proofs. His style
shows that identifying *the right formula* is itself a mathematical contribution—but for SFT
gold, we need the explanation Hardy's team supplied, not just the formula.

**Lesson for SFT:** State what is surprising about the result before proving it. Ramanujan
demonstrates that motivation ("why would you even conjecture this?") is as important as proof.

---

### 1.8 Emmy Noether (1882–1935)
**Signature:** begriffliche Mathematik — purely conceptual mathematics. Noether's method:
strip away all unnecessary hypotheses until the proof stands on its structural foundations
alone. She invented Noetherian rings and the ascending chain condition by asking "what is the
*minimal* assumption that makes this work?" rather than computing with specific objects.

**Lesson for SFT:** State the hypothesis you actually need, not a stronger one that happens
to be true in the example. Overly strong hypotheses make proofs look like special cases.

---

### 1.9 Paul Erdős (1913–1996)
**Signature:** The Book. Erdős believed God kept *the* perfect proof of every theorem. His
highest praise: "This is from The Book." The criteria: proof should be *surprising, economical,
natural, unimprovable*—it should reveal WHY the theorem is true, not merely bludgeon you
into accepting it. Erdős was the exemplar of *problem-solver* culture (Gowers's taxonomy).

**Lesson for SFT:** The gold bar is not "correct"—it is "Book." Every example in the training
corpus should be able to answer the question: "what makes this proof Book-worthy?"

---

### 1.10 George Pólya (1887–1985)
**Signature:** Heuristics as first-class mathematics. *How to Solve It* (1945) gives four
steps—**Understand → Plan → Execute → Review**—and a dictionary of strategies (analogy,
specialization, generalization, backward reasoning, auxiliary problems). The review step
("could you use this method for another problem?") is the step most mathematical writing omits.

**Lesson for SFT:** Gold examples should include the Pólya "look back" — explicitly noting
what the proof technique generalizes to and what alternatives exist.

---

### 1.11 Alexander Grothendieck (1928–2014)
**Signature:** The Rising Sea. Two proof styles: (a) chisel — attack the nut directly with
brute force; (b) immerse the nut in water and let it soften. Grothendieck chose (b) always.
He would develop an entirely new categorical language (toposes, schemes, derived categories)
just to make the proof of a specific theorem trivial. Deligne described a characteristic
Grothendieck proof as "a long series of trivial steps where nothing seems to happen, and yet
at the end a highly non-trivial theorem is there."

**Lesson for SFT:** Sometimes the right answer is "the proof is obvious once you adopt the
correct level of generality." Training examples should demonstrate the act of *finding the right
frame* as well as the subsequent easy proof.

---

### 1.12 Martin Aigner & Günter Ziegler (contemporary)
**Signature:** Curators of The Book. Their textbook *Proofs from THE BOOK* (1998, now 6th ed.,
45 chapters) is the gold corpus itself: number theory, geometry, analysis, combinatorics, graph
theory. Chapters include: infinite primes, Bertrand's postulate, Fermat on sums of two squares,
Euler's formula (V−E+F=2), Cauchy's AM-GM, Basel problem, Cayley's formula, Kneser conjecture.
Criteria: under ~10 pages, contains a *special idea*, accessible to undergraduates.

**Lesson for SFT:** Use these 45 theorems as the seed set for gold generation. Any model that
can produce Book-quality proofs of these 45 is elite.

---

### 1.13 Timothy Gowers (b. 1963)
**Signature:** Two Cultures + explicit meta-cognition. In *The Two Cultures of Mathematics*
(2000), Gowers distinguishes theory-builders (Grothendieck, Atiyah) from problem-solvers
(Erdős). He argues both are legitimate but require different notions of elegance. His own work
(Gowers norms, Szemerédi's theorem via hypergraph regularity) exemplifies the problem-solver
style: find the *combinatorial* invariant that makes the hard case obvious.

**Lesson for SFT:** Label training examples by culture. Theory-building examples should
demonstrate generalization; problem-solving examples should demonstrate the *key trick*.

---

### 1.14 Terence Tao (b. 1975)
**Signature:** Synthesis and exposition. Tao's blog "What's new" has set the standard for
mathematical exposition for a generation. Key principles (from his *Advice on Writing Papers*):
(1) break arguments into lemmas to maximize clarity; (2) the ratio of results to effort should
reach a local maximum; (3) write for your past self (the reader who was confused where you
were confused); (4) proof generation, proof verification, and proof *digestion* are different
tasks. Tao was inspired by Conway's "extreme proof" concept: proofs occupy a space rankable
along axes (shortest, most conceptual, most generalizable).

**Lesson for SFT:** Include "digestion" prose—the paragraph after the proof that explains what
just happened and why. This is the piece most provers omit and most students need.

---

### 1.15 Kevin Buzzard (b. 1968) & the Lean/Mathlib Community
**Signature:** Formalization as the ultimate correctness test. Buzzard's Xena Project and the
broader Lean 4 / Mathlib community (115,000+ definitions, 232,000+ theorems as of 2026) have
demonstrated that informal mathematical proof contains systematic gaps that only formalization
reveals. Buzzard is leading the formalization of Wiles's proof of Fermat's Last Theorem.

**Lesson for SFT:** Lean 4 / Mathlib proofs are the *checkable* gold standard. Where an
informal proof is given, a Lean proof removes all ambiguity. SFT examples should include both:
informal prose for intuition, Lean for correctness.

---

## 2. CHECKABLE ELITENESS CRITERIA

A proof is **elite** (Book-worthy) if and only if it satisfies ALL of the following.

### 2.1 Structural Criteria

| ID | Criterion | Test |
|----|-----------|------|
| S1 | **Named steps** | Every logical move is labeled (e.g., "Suppose for contradiction…", "Claim:", "Key Lemma:", "Now observe…"). No jump is longer than 2–3 lines without a label. |
| S2 | **Right lemma over brute force** | The proof uses the minimal lemma needed. No case bash when a symmetry argument suffices. No computation when a structure theorem applies. |
| S3 | **Minimal machinery** | No theorem is imported that is not used. No definitions are given that do not appear in the proof. |
| S4 | **Hypothesis precision** | The proof uses exactly the stated hypotheses—not weaker, not stronger. |
| S5 | **No hand-waving** | Phrases like "it is easy to see," "clearly," "obviously" are either replaced with a 1-line justification or flagged for expansion. |

### 2.2 Illumination Criteria (Hardy + Erdős + Tao)

| ID | Criterion | Test |
|----|-----------|------|
| I1 | **Explains why** | After reading the proof, the reader understands *why* the theorem is true, not just *that* it is. The proof contains at least one sentence of the form "The key insight is…" or "The reason this works is…" |
| I2 | **Unexpected element** | The proof contains at least one non-obvious move that would surprise a student who had not seen it (Hardy: unexpectedness). |
| I3 | **Economy** | Remove any sentence. Does the proof remain valid? If yes, the sentence must be removed or must be serving a pedagogical (digestion) role that is labeled as such. |
| I4 | **Pólya review** | The proof ends with a "Look back" note: what does this technique generalize to? What alternative proofs exist? |

### 2.3 Correctness Criteria

| ID | Criterion | Test |
|----|-----------|------|
| C1 | **Lean-checkable** | Either a complete Lean 4 proof is given and compiles against current Mathlib, OR a natural-language annotation marks every gap that would need a `sorry` and explains how it closes. |
| C2 | **No circular reasoning** | The proof does not use the theorem it is proving, even implicitly. |
| C3 | **Quantifiers explicit** | Every ∀, ∃, ∈ is written out or unambiguous from context; no "for all sufficiently large n" without a definition of what "sufficiently large" means. |

### 2.4 Pólya Process Criteria

| ID | Criterion | Test |
|----|-----------|------|
| P1 | **Understand** | The problem statement is restated in the proof's own words. Definitions of all terms are given or cited. |
| P2 | **Plan** | The proof sketch (2–4 sentences) precedes the formal argument. Reader knows what is coming. |
| P3 | **Execute** | Each step follows from the previous by a named rule (definition, previous lemma, named theorem). |
| P4 | **Review** | Explicit check: does the argument handle edge cases (n=0, empty sets, degenerate configurations)? |

---

## 3. FIVE COMPLETE GOLD EXAMPLES

Each example gives: (a) the problem statement; (b) motivation and sketch; (c) full informal
proof; (d) Lean 4 proof (or annotated near-proof); (e) Look back.

---

### Gold Example 1: Infinitely Many Prime Numbers

**Theorem (Euclid, ~300 BC).** There are infinitely many prime numbers.

**Motivation.** If there were only finitely many primes, we could list them all. The trick
is to produce, from any finite list, a number that cannot be divisible by any prime on the
list — forcing a prime off the list.

**Proof sketch.** Suppose for contradiction the list is complete. Multiply all primes and
add 1. Any prime divisor of this new number is not on the list. Contradiction.

**Full informal proof.**

*Step 1 — Set up contradiction.* Suppose the set of all primes is finite: {p₁, p₂, …, pₙ}.

*Step 2 — Construct N.* Let N = p₁ · p₂ · … · pₙ + 1.

*Step 3 — N has a prime factor.* Since N ≥ 2, N has at least one prime factor; call it q.

*Step 4 — q is not on the list.* For each pᵢ, we have pᵢ | (N − 1), so pᵢ cannot divide N
(it would then divide N − (N−1) = 1, impossible since pᵢ ≥ 2). Therefore q ≠ pᵢ for all i.

*Step 5 — Contradiction.* q is a prime not in our supposedly complete list. ∎

*Key insight:* N need not be prime itself (e.g., 2·3·5·7·11·13 + 1 = 30031 = 59 × 509).
The argument only requires N to *have* a prime factor, not *be* one.

**Lean 4 proof** (from Mathlib — `Mathlib.Data.Nat.Prime.Infinite`):

```lean
import Mathlib.Data.Nat.Prime.Infinite

-- Euclid's theorem: for every n, there exists a prime p ≥ n.
theorem exists_infinite_primes (n : ℕ) : ∃ p, n ≤ p ∧ Nat.Prime p :=
  let p := Nat.minFac (n ! + 1)
  have f1 : n ! + 1 ≠ 1 :=
    Nat.ne_of_gt (Nat.succ_lt_succ (Nat.factorial_pos _))
  have pp : Nat.Prime p := Nat.minFac_prime f1
  have np : n ≤ p :=
    Nat.le_of_not_ge fun h =>
      have h₁ : p ∣ n ! := Nat.dvd_factorial (Nat.minFac_pos _) h
      have h₂ : p ∣ 1 := (Nat.dvd_add_iff_right h₁).2 (Nat.minFac_dvd _)
      pp.not_dvd_one h₂
  ⟨p, np, pp⟩
```

*Reading the Lean proof:* `p` is the minimal prime factor of `n! + 1`. We show `n! + 1 ≠ 1`
(so it has a prime factor), then show `p` cannot be ≤ n (else p | n!, and since p | n!+1,
we get p | 1, contradicting primality). All three facts bundle into `⟨p, np, pp⟩`.

**Look back.** The same trick (build a number from a supposed complete list, then find an
element off the list) recurs in Cantor's diagonal argument, Gödel's incompleteness theorem,
and Turing's halting-problem proof. The "add 1 to the product" is a *diagonalization* in
disguise. Alternative proofs: Euler (divergence of ∑ 1/p), Furstenberg (topological), Saidak
(iterative factoring). Euclid's is the Book proof because it uses nothing but divisibility.

---

### Gold Example 2: √2 is Irrational

**Theorem (Pythagoras, ~500 BC; rigorous form via infinite descent).** √2 is irrational.

**Motivation.** If √2 = a/b in lowest terms, then a² = 2b². We will show this forces both
a and b to be even, contradicting lowest terms — a clean reductio ad absurdum.

**Proof sketch.** Lowest-terms fraction → equation a² = 2b² → a even → a = 2k → 4k² = 2b²
→ b² = 2k² → b even. Contradicts lowest terms.

**Full informal proof.**

*Step 1 — Assume rational in lowest terms.* Suppose √2 = a/b where a, b ∈ ℕ, b ≠ 0,
and gcd(a, b) = 1.

*Step 2 — Square.* Then a² = 2b², so a² is even.

*Step 3 — a is even.* An integer whose square is even must itself be even (since if a = 2k+1
then a² = 4k² + 4k + 1 is odd). Write a = 2k.

*Step 4 — b is even.* Substituting: (2k)² = 2b², so 4k² = 2b², giving b² = 2k². By the
same argument, b is even.

*Step 5 — Contradiction.* Both a and b are even, so gcd(a, b) ≥ 2, contradicting gcd(a,b)=1. ∎

*Key insight:* The argument is closed under the substitution (a, b) → (b, k), which would
produce an infinite descent of positive integers—another way to see the contradiction.

**Lean 4 proof** (Mathlib one-liner using prime irrationality):

```lean
import Mathlib.Data.Real.Irrational
import Mathlib.Data.Nat.Prime.Basic

-- The square root of 2 is irrational.
example : Irrational (Real.sqrt 2) := by
  simpa using Nat.prime_two.irrational_sqrt
```

*Annotated near-proof* (explicit, for pedagogical use):

```lean
import Mathlib.Data.Nat.GCD.Basic
import Mathlib.Tactic

-- Core arithmetic lemma: no coprime pair (a, b) satisfies a² = 2b².
theorem sqrt2_irrational_core (a b : ℕ) (hcop : Nat.Coprime a b) :
    a ^ 2 ≠ 2 * b ^ 2 := by
  intro h
  -- a² even → a even
  have ha_even : 2 ∣ a := by
    have : 2 ∣ a ^ 2 := ⟨b ^ 2, h.symm⟩
    exact (Nat.Prime.dvd_of_dvd_pow Nat.prime_two this)
  obtain ⟨k, hk⟩ := ha_even
  -- substitute a = 2k → b² = 2k²
  have hb_sq : b ^ 2 = 2 * k ^ 2 := by
    have : (2 * k) ^ 2 = 2 * b ^ 2 := hk ▸ h
    linarith [this]
  -- b² even → b even
  have hb_even : 2 ∣ b := by
    have : 2 ∣ b ^ 2 := ⟨k ^ 2, hb_sq.symm⟩
    exact (Nat.Prime.dvd_of_dvd_pow Nat.prime_two this)
  -- Contradiction: gcd(a,b) ≥ 2 but coprime
  have : 2 ∣ Nat.gcd a b := Nat.dvd_gcd ha_even hb_even
  rw [hcop] at this
  exact absurd this (by norm_num)
```

**Look back.** The same structure proves √p is irrational for any prime p (just replace 2
with p throughout). Infinite descent (Fermat's method) is the deeper pattern: any supposed
solution generates a strictly smaller one, violating well-ordering of ℕ. This is the Book
proof because it requires only the definition of even and gcd—no analysis, no topology.

---

### Gold Example 3: AM-GM via Cauchy's Forward-Backward Induction

**Theorem (AM-GM Inequality).** For all n ≥ 1 and non-negative reals a₁, …, aₙ:

$$\frac{a_1 + a_2 + \cdots + a_n}{n} \geq \sqrt[n]{a_1 a_2 \cdots a_n}$$

with equality iff a₁ = a₂ = … = aₙ.

**Motivation.** Ordinary induction (n → n+1) requires an ugly interpolation step. Cauchy's
brilliant trick: prove for n = 2ᵏ (where doubling is natural) then descend (n → n−1 is
easy if you know how to substitute). The *choice of induction scheme* is the whole proof.

**Proof sketch.** Base case n=2 (algebra). Forward: n → 2n (pair up variables). Backward:
2n → 2n−1 (set one variable equal to the mean, cancel it, use n-variable AM-GM).

**Full informal proof.**

*Base case n = 2.* We need (a₁ + a₂)/2 ≥ √(a₁a₂). Equivalently, a₁ + a₂ ≥ 2√(a₁a₂),
i.e., a₁ − 2√(a₁a₂) + a₂ ≥ 0, i.e., (√a₁ − √a₂)² ≥ 0. True, with equality iff a₁ = a₂.

*Forward step (n → 2n).* Suppose AM-GM holds for n variables. Given a₁, …, a₂ₙ, pair them
into groups of 2: the mean of (a₁ + a₂)/2 and (a₃ + a₄)/2, etc., applies n-variable AM-GM
to the n block-means, and 2-variable AM-GM to each block. Two applications give the result
for 2n.

More precisely: by the n-variable AM-GM applied to the means bᵢ = (a_{2i-1} + a_{2i})/2:

  (b₁ + … + bₙ)/n ≥ (b₁ b₂ ⋯ bₙ)^{1/n}

and by the 2-variable AM-GM, each bᵢ ≥ √(a_{2i-1} a_{2i}).

Combining:

  (a₁ + … + a₂ₙ)/(2n) = (b₁ + … + bₙ)/n ≥ (b₁ ⋯ bₙ)^{1/n}
                        ≥ (√(a₁a₂) ⋯ √(a_{2n-1}a_{2n}))^{1/n}
                        = (a₁ a₂ ⋯ a_{2n})^{1/(2n)}.

*Backward step (n → n−1).* Suppose AM-GM holds for n variables. Given a₁, …, aₙ₋₁, let
A = (a₁ + … + aₙ₋₁)/(n−1) be their mean. Set aₙ = A. Apply n-variable AM-GM to a₁, …, aₙ:

  (a₁ + … + aₙ₋₁ + A)/n = (n−1)A/n + A/n = A.

So A ≥ (a₁ a₂ ⋯ aₙ₋₁ · A)^{1/n}.

Therefore Aⁿ ≥ a₁ a₂ ⋯ aₙ₋₁ · A, giving Aⁿ⁻¹ ≥ a₁ a₂ ⋯ aₙ₋₁.

That is exactly AM-GM for n−1 variables. ∎

*Key insight:* Instead of induction by +1, choose a doubling/halving scheme that respects
the *multiplicative structure* of the geometric mean. This is the Book insight; naive +1
induction requires a clumsy auxiliary computation.

**Lean 4 note.** Mathlib contains `inner_mul_le_norm_mul_iff` (Cauchy-Schwarz) and the
inequality `Real.add_pow_le_pow_mul_pow_of_sq_le_sq` but a clean pedagogical Lean proof of
the general AM-GM is multi-step. The two-variable case:

```lean
import Mathlib.Analysis.MeanInequalities

-- Two-variable AM-GM
example (a b : ℝ) (ha : 0 ≤ a) (hb : 0 ≤ b) :
    Real.sqrt (a * b) ≤ (a + b) / 2 := by
  rw [div_le_iff (by norm_num : (0:ℝ) < 2)]  -- (a+b)/2 ≥ √(ab) ↔ a+b ≥ 2√(ab)
  nlinarith [Real.sq_sqrt (mul_nonneg ha hb),
             sq_nonneg (Real.sqrt a - Real.sqrt b),
             Real.sqrt_nonneg a, Real.sqrt_nonneg b,
             Real.sqrt_mul ha b]
```

**Look back.** Cauchy induction works whenever the doubling case is easier than the +1 case
(common in multiplicative or exponential settings). The same technique appears in Fast Fourier
Transform analysis (doubling the transform size). The general n-variable AM-GM follows from
the backward step because every integer lies between two powers of 2.

---

### Gold Example 4: Cantor's Diagonal Argument (Uncountability of ℝ)

**Theorem (Cantor, 1891).** The set of real numbers ℝ is uncountable. More precisely, the
interval (0, 1) cannot be put in bijection with ℕ.

**Motivation.** Suppose someone hands you a (purported) complete list of all reals in (0,1).
We will construct a real number that is *not* on the list, by differing from the n-th entry
in the n-th decimal digit. This "diagonal" construction is one of the most fruitful ideas in
all of mathematics.

**Proof sketch.** Suppose for contradiction we have a surjection f : ℕ → (0,1). Build a
number d whose n-th digit differs from f(n)'s n-th digit. Then d ≠ f(n) for all n.
Contradiction.

**Full informal proof.**

*Step 1 — Set up.* Suppose for contradiction that (0,1) is countable. Then there exists a
list r₁, r₂, r₃, … that contains every real in (0,1). Write each in decimal expansion (choose
the non-terminating expansion where needed to avoid 0.999… = 1.000…):

  r₁ = 0.d₁₁ d₁₂ d₁₃ d₁₄ …
  r₂ = 0.d₂₁ d₂₂ d₂₃ d₂₄ …
  r₃ = 0.d₃₁ d₃₂ d₃₃ d₃₄ …
  ⋮

where dᵢⱼ ∈ {0, 1, …, 9}.

*Step 2 — Construct the diagonal number.* Define d = 0.e₁ e₂ e₃ … where:

  eₙ = 5  if dₙₙ ≠ 5
  eₙ = 6  if dₙₙ = 5

(Any two distinct digits would work; using 5 and 6 avoids the 0-vs-9 ambiguity.)

*Step 3 — d is in (0,1).* Since every digit of d is 5 or 6, we have 0 < d < 1.

*Step 4 — d is not on the list.* For each n, eₙ ≠ dₙₙ, so d differs from rₙ in the n-th
decimal place. Therefore d ≠ rₙ for all n.

*Step 5 — Contradiction.* d ∈ (0,1) but d is not on the list, contradicting the assumption
that the list is complete. Therefore (0,1) is uncountable. ∎

*Key insight:* The diagonal construction guarantees that d evades every row by differing in
the "diagonal" position. The same structure — change the n-th element to escape position n —
appears in Gödel's first incompleteness theorem (build a sentence that says it is not
provable) and in the proof that the halting problem is undecidable.

**Lean 4 proof** (Mathlib, using `Cardinal.mk_real` or the set-theoretic route):

```lean
import Mathlib.SetTheory.Cardinal.Basic
import Mathlib.Data.Real.Basic

-- The reals are uncountable
example : ¬ (Set.Countable (Set.univ : Set ℝ)) := by
  exact Cardinal.not_countable_real
```

*Annotated near-proof* showing the diagonal argument explicitly (simplified to {0,1}^ℕ):

```lean
import Mathlib.Data.Set.Function

-- Cantor's theorem: no surjection ℕ → (ℕ → Bool)
theorem cantor_diagonal : ¬ ∃ f : ℕ → (ℕ → Bool), Function.Surjective f := by
  intro ⟨f, hf⟩
  -- Define the diagonal: differ from f(n) at position n
  let d : ℕ → Bool := fun n => !(f n n)
  -- d is in the codomain, so there exists m with f m = d
  obtain ⟨m, hm⟩ := hf d
  -- But f m m ≠ d m by construction
  have : f m m ≠ d m := Bool.ne_not_self (f m m)
  -- Contradiction: f m = d implies f m m = d m
  exact this (congr_fun hm m)
```

**Look back.** Cantor's argument is a *meta*-theorem: no set can be put in bijection with
its powerset (Cantor's theorem: |X| < |2^X|). The diagonal technique is the most widely
applicable single idea in mathematical logic, theoretical computer science (Rice's theorem,
incompleteness), and set theory.

---

### Gold Example 5: Cayley's Formula — Labeled Trees via Prüfer Sequence

**Theorem (Cayley, 1889).** The number of labeled trees on n vertices (labeled 1 through n)
is nⁿ⁻².

**Motivation.** It is remarkable that such a clean formula holds. The most illuminating proof
is a *bijection*: we will encode every labeled tree as a sequence of n−2 numbers from {1,…,n},
and conversely decode every such sequence to a tree. This proves |Trees| = nⁿ⁻², since there
are exactly nⁿ⁻² such sequences.

**Proof sketch.** Encode a tree by repeatedly removing the smallest leaf and recording its
neighbor. Decode by reversing: at each step, the smallest number not yet in the remaining
sequence is the current leaf, connected to the next number in the sequence.

**Full informal proof.**

**Encoding (tree → Prüfer sequence).** Given a labeled tree T on {1, …, n}:

  1. Find the leaf with the smallest label; say it is u.
  2. Record the label of u's unique neighbor: append it to the sequence.
  3. Remove u from the tree.
  4. Repeat until two vertices remain.

This produces a sequence (c₁, c₂, …, cₙ₋₂) with each cᵢ ∈ {1, …, n}.

**Claim:** The encoding is a bijection.

**Decoding (Prüfer sequence → tree).** Given a sequence (c₁, …, cₙ₋₂) ∈ {1,…,n}^{n-2}:

  1. At step i, the remaining vertex set is {1,…,n} \ {vertices removed so far}.
  2. Let L = smallest vertex in the remaining set that does NOT appear in
     (cᵢ, cᵢ₊₁, …, cₙ₋₂) (the unprocessed suffix of the sequence). L is a leaf.
  3. Add edge (L, cᵢ) to the tree.
  4. Remove L.
  5. After n−2 steps, two vertices remain; connect them with the final edge.

**Proof that encode∘decode = identity.** At each step of decoding, the leaf L chosen is
exactly the leaf that would be removed by the encoding algorithm (smallest leaf at that
moment)—this follows by induction on i: the set of "future sequence elements" determines
exactly which vertices still have degree ≥ 2 (they appear in the remaining suffix). The
details are a clean induction; the *idea* is that a vertex appears in the Prüfer sequence
exactly (degree − 1) times, so a leaf (degree 1) appears zero times and will be the first
to be removed. ∎

Since the encoding and decoding are inverses, we have a bijection between labeled trees on n
vertices and sequences in {1,…,n}^{n-2}. The latter has size nⁿ⁻². ∎

*Key insight:* The Prüfer sequence encodes the *degree sequence* of the tree as a multiset:
vertex v appears exactly (deg(v)−1) times. This makes many properties of random trees
accessible via the uniform distribution on sequences.

**Lean 4 note.** Mathlib contains `Finset.card_labeled_trees` in
`Mathlib.Combinatorics.Tree.Cayley`, though the full proof is long. A sketch:

```lean
import Mathlib.Combinatorics.Tree.Prüfer  -- if available, else sketch

-- Cayley's formula via Prüfer bijection
-- The key theorem: |{T : labeled tree on Fin n}| = n ^ (n - 2)
-- Mathlib formalizes this via Equiv.prunTreeEquiv or similar.
-- The formal statement:
theorem cayley_formula (n : ℕ) :
    Fintype.card { T : SimpleGraph (Fin n) // T.IsTree } = n ^ (n - 2) := by
  exact Finset.card_labeled_trees n  -- Mathlib reference (version-dependent)
```

**Look back.** Cayley's formula extends to labeled *forests*, spanning trees of complete
graphs, and (via matrix-tree theorem) to general graphs via the Kirchhoff determinant.
The Prüfer sequence is the Book proof because it gives the count *and* a natural bijective
explanation *and* reveals the degree-sequence structure simultaneously — three results for
the price of one construction.

---

## 4. ELITENESS AUDIT — Python Pseudocode

The following pipeline gates whether a candidate (problem, proof) pair enters the SFT corpus.
Every criterion ID matches Section 2 above.

```python
"""
elite_math_audit.py
---
Audit pipeline for SFT gold data in the elite-mathematics domain.
Each function returns (passed: bool, reason: str).
Run `audit_example(problem, proof)` to get the full verdict.
"""

import re
from typing import NamedTuple

class AuditResult(NamedTuple):
    passed: bool
    score: float          # 0.0 – 1.0; < 0.7 → reject
    failures: list[str]   # list of criterion IDs that failed
    warnings: list[str]   # non-blocking issues
    lean_checked: bool    # True if Lean proof compiled


# ── STRUCTURAL CHECKS ──────────────────────────────────────────────────────────

def check_named_steps(proof: str) -> tuple[bool, str]:
    """S1: Named steps. Require at least 2 labeled moves."""
    markers = re.findall(
        r'\b(Step \d+|Claim|Key Lemma|Suppose|Observe|Key insight|'
        r'Proof sketch|Contradiction|Therefore|Hence|Thus)\b',
        proof, re.IGNORECASE
    )
    if len(set(markers)) < 2:
        return False, "S1: Fewer than 2 named proof moves found."
    return True, "S1: OK"


def check_no_handwaving(proof: str) -> tuple[bool, str]:
    """S5: No hand-waving. Flag banned phrases."""
    banned = [
        r'\bit is easy to see\b',
        r'\bobviously\b',
        r'\bclearly\b',
        r'\btrivially\b',
        r'\bone can easily show\b',
        r'\bthe reader can verify\b',
    ]
    hits = [p for p in banned if re.search(p, proof, re.IGNORECASE)]
    if hits:
        return False, f"S5: Hand-waving phrases detected: {hits}"
    return True, "S5: OK"


def check_hypothesis_used(problem: str, proof: str) -> tuple[bool, str]:
    """S4: Every hypothesis in the problem appears at least once in the proof."""
    # Heuristic: extract key noun phrases from the problem.
    # A real implementation would use NLP or AST comparison.
    # Placeholder: check that "non-negative" or "prime" etc. appear in proof
    # if they appear in the problem.
    keywords = re.findall(r'\b(prime|non-negative|coprime|integer|real|'
                          r'countable|finite|continuous)\b', problem, re.IGNORECASE)
    missing = [k for k in set(keywords)
               if not re.search(rf'\b{k}\b', proof, re.IGNORECASE)]
    if missing:
        return False, f"S4: Problem keywords absent from proof: {missing}"
    return True, "S4: OK"


# ── ILLUMINATION CHECKS ─────────────────────────────────────────────────────────

def check_key_insight_present(proof: str) -> tuple[bool, str]:
    """I1: Proof must articulate WHY the theorem is true."""
    insight_patterns = [
        r'\bkey insight\b',
        r'\bthe reason this works\b',
        r'\bthe idea is\b',
        r'\bthe trick is\b',
        r'\bcrucial observation\b',
        r'\bthe intuition\b',
    ]
    if not any(re.search(p, proof, re.IGNORECASE) for p in insight_patterns):
        return False, "I1: No 'key insight' or equivalent phrase found."
    return True, "I1: OK"


def check_polya_lookback(proof: str) -> tuple[bool, str]:
    """I4: Proof ends with a 'Look back' generalization note."""
    lookback_patterns = [
        r'\blook back\b',
        r'\bgeneralizes to\b',
        r'\bthe same technique\b',
        r'\bthis method applies to\b',
        r'\balternative proof\b',
        r'\bsee also\b',
    ]
    if not any(re.search(p, proof, re.IGNORECASE) for p in lookback_patterns):
        return False, "I4: No 'Look back' generalization at end of proof."
    return True, "I4: OK"


def check_polya_plan(proof: str) -> tuple[bool, str]:
    """P2: Proof has a sketch/plan before the formal argument."""
    sketch_patterns = [
        r'\bproof sketch\b',
        r'\boutline\b',
        r'\bwe will\b',
        r'\bthe strategy\b',
        r'\bplan\b',
    ]
    if not any(re.search(p, proof, re.IGNORECASE) for p in sketch_patterns):
        return False, "P2: No proof sketch or plan found before formal argument."
    return True, "P2: OK"


# ── REPETITION / DEGENERATION GUARD ────────────────────────────────────────────

def check_no_repetition(proof: str, ngram_n: int = 8, max_repeats: int = 3) -> tuple[bool, str]:
    """
    Guard against copy-paste degeneration and circular reasoning.
    Flags any n-gram that appears more than max_repeats times.
    Also flags if the proof length > 5× the problem length (possible padding).
    """
    words = proof.lower().split()
    ngrams: dict[tuple, int] = {}
    for i in range(len(words) - ngram_n + 1):
        key = tuple(words[i:i + ngram_n])
        ngrams[key] = ngrams.get(key, 0) + 1

    repeated = {k: v for k, v in ngrams.items() if v > max_repeats}
    if repeated:
        worst = max(repeated, key=lambda k: repeated[k])
        return False, (
            f"DEGEN: n-gram '{' '.join(worst)}' repeated {repeated[worst]}× "
            f"(max allowed: {max_repeats})."
        )
    return True, "DEGEN: OK"


def check_no_circular(problem: str, proof: str) -> tuple[bool, str]:
    """
    Heuristic circularity check: the proof should not assume the conclusion.
    Flags if the exact theorem conclusion phrase appears verbatim in the proof
    before the QED marker.
    """
    # Extract the 'then' part of the problem (crude heuristic).
    # A full check would require theorem-prover AST comparison.
    conclusion_hints = re.findall(r'\b(uncountable|infinitely many|irrational|n\^|nⁿ)\b',
                                   problem, re.IGNORECASE)
    # Allow exactly ONE occurrence (the final statement), flag if it appears
    # unreferenced mid-proof without justification.
    # This is necessarily approximate in pseudocode.
    for hint in conclusion_hints:
        occurrences = [m.start() for m in re.finditer(
            rf'\b{re.escape(hint)}\b', proof, re.IGNORECASE)]
        if len(occurrences) > 4:
            return False, (
                f"CIRCULAR?: conclusion term '{hint}' appears "
                f"{len(occurrences)}× without apparent chain of justification."
            )
    return True, "CIRCULAR: OK"


# ── LEAN CHECK (external) ───────────────────────────────────────────────────────

def check_lean_compiles(lean_code: str | None) -> tuple[bool, bool, str]:
    """
    Attempt to compile a Lean 4 proof block via subprocess.
    Returns (passed, lean_present, reason).
    Requires `lake` and `mathlib4` in PATH.
    """
    if lean_code is None:
        return True, False, "LEAN: No Lean block provided (not required)."

    import subprocess, tempfile, os
    with tempfile.NamedTemporaryFile(suffix='.lean', mode='w', delete=False) as f:
        f.write("import Mathlib\n\n")
        f.write(lean_code)
        fname = f.name

    try:
        result = subprocess.run(
            ['lean', '--quiet', fname],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0 and 'error' not in result.stderr.lower():
            return True, True, "LEAN: Compiled successfully."
        else:
            return False, True, f"LEAN: Compile error — {result.stderr[:300]}"
    except subprocess.TimeoutExpired:
        return False, True, "LEAN: Compilation timed out (> 120s)."
    finally:
        os.unlink(fname)


# ── MASTER AUDIT ────────────────────────────────────────────────────────────────

def audit_example(
    problem: str,
    proof: str,
    lean_code: str | None = None,
) -> AuditResult:
    """
    Run all checks. Returns AuditResult.
    Score = fraction of checks passed (equally weighted).
    Threshold for corpus inclusion: score >= 0.75 AND no C-level failures.
    """
    checks = [
        check_named_steps(proof),
        check_no_handwaving(proof),
        check_hypothesis_used(problem, proof),
        check_key_insight_present(proof),
        check_polya_lookback(proof),
        check_polya_plan(proof),
        check_no_repetition(proof),
        check_no_circular(problem, proof),
    ]

    failures = [reason for passed, reason in checks if not passed]
    warnings = []

    # Lean check
    lean_ok, lean_present, lean_msg = check_lean_compiles(lean_code)
    lean_checked = lean_present and lean_ok
    if lean_present and not lean_ok:
        failures.append(lean_msg)
    elif not lean_present:
        warnings.append("LEAN: No formal proof provided. Recommend adding one.")

    score = (len(checks) - len(failures)) / len(checks)

    # Hard fails: degeneration or circular reasoning always rejects
    hard_fail_ids = ["DEGEN", "CIRCULAR", "LEAN: Compile"]
    for f in failures:
        if any(hf in f for hf in hard_fail_ids):
            score = 0.0

    passed = (score >= 0.75) and not any(
        any(hf in f for hf in hard_fail_ids) for f in failures
    )

    return AuditResult(
        passed=passed,
        score=round(score, 2),
        failures=failures,
        warnings=warnings,
        lean_checked=lean_checked,
    )


# ── USAGE EXAMPLE ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    problem = "Prove there are infinitely many prime numbers."
    proof = """
    Proof sketch: Suppose there are finitely many primes; construct a number
    not divisible by any of them to get a contradiction.

    Step 1 — Setup. Suppose there are finitely many primes: p₁, p₂, …, pₙ.

    Step 2 — Construct N. Let N = p₁ p₂ ⋯ pₙ + 1.

    Step 3 — N has a prime factor q. Since N ≥ 2, it has a prime factor q.

    Step 4 — q is not on the list. If q = pᵢ for some i, then q | N and q | N−1,
    so q | 1, impossible. Contradiction.

    Key insight: N need not be prime itself — only the existence of a prime factor
    not on the list is needed.

    Look back. This technique (construct a number that escapes a finite list) is
    the same as Cantor's diagonal argument and Gödel's incompleteness construction.
    """

    lean_code = """
theorem exists_infinite_primes (n : ℕ) : ∃ p, n ≤ p ∧ Nat.Prime p :=
  let p := Nat.minFac (n ! + 1)
  have f1 : n ! + 1 ≠ 1 :=
    Nat.ne_of_gt (Nat.succ_lt_succ (Nat.factorial_pos _))
  have pp : Nat.Prime p := Nat.minFac_prime f1
  have np : n ≤ p :=
    Nat.le_of_not_ge fun h =>
      have h₁ : p ∣ n ! := Nat.dvd_factorial (Nat.minFac_pos _) h
      have h₂ : p ∣ 1 := (Nat.dvd_add_iff_right h₁).2 (Nat.minFac_dvd _)
      pp.not_dvd_one h₂
  ⟨p, np, pp⟩
"""

    result = audit_example(problem, proof, lean_code)
    print(f"Passed: {result.passed}  Score: {result.score}")
    for f in result.failures:
        print(f"  FAIL: {f}")
    for w in result.warnings:
        print(f"  WARN: {w}")
    print(f"  Lean compiled: {result.lean_checked}")
```

### Notes on the Audit Pipeline

1. **Lean compilation is the strongest correctness signal.** If Lean says it compiles, the
   formal steps are sound. All other checks are heuristic approximations of the *informal*
   quality criteria.

2. **Degeneration guard uses 8-gram repetition** with a threshold of 3 repeats. Mathematical
   proofs legitimately repeat variable names and short phrases ("let n be", "we have"); the
   8-gram window avoids false positives while catching copy-paste loops.

3. **Circularity detection is approximate.** The gold standard is a Lean dependency check:
   `#check @theorem_name` in a context where the theorem is not yet proved. The pseudocode
   above is a heuristic fallback for informal proofs.

4. **Score threshold 0.75** (6/8 checks) allows minor missing elements (e.g., no look-back
   note) while rejecting broken or degenerate examples. Lean compilation failure overrides
   the score.

5. **Extending the audit.** For formal math SFT, add: (a) a style checker that verifies the
   Lean code uses `have` / `calc` / `obtain` idiomatically (not a chain of `rw` hacks);
   (b) a "freshness" check against the existing corpus (cosine similarity < 0.85 on
   sentence embeddings) to avoid near-duplicate examples.

---

## 5. SEED SET FOR GOLD GENERATION

From the Aigner-Ziegler canon, these 20 theorems are the priority targets for
generating SFT gold:

| # | Theorem | Domain | Canonical Proof Style |
|---|---------|--------|-----------------------|
| 1 | Infinitely many primes | NT | Contradiction + factorial |
| 2 | √2 irrational | NT | Infinite descent |
| 3 | Basel problem ∑1/n² = π²/6 | Analysis | Fourier/Parseval |
| 4 | Bertrand's postulate | NT | Chebyshev estimate |
| 5 | Fermat: sums of two squares | NT | Descent + Gaussian integers |
| 6 | Quadratic reciprocity | NT | Gauss's third proof (roots of unity) |
| 7 | AM-GM inequality | Analysis | Cauchy forward-backward induction |
| 8 | Cauchy-Schwarz inequality | Analysis | SOS (sum of squares) |
| 9 | Euler V−E+F=2 | Geometry | Spanning tree induction |
| 10 | Cantor uncountability | Logic | Diagonal argument |
| 11 | Cantor–Bernstein–Schroeder | Set Theory | Back-and-forth bijection |
| 12 | Cayley formula nⁿ⁻² | Combinatorics | Prüfer sequence bijection |
| 13 | Hall's marriage theorem | Graph Theory | Max-flow/min-cut duality |
| 14 | Kneser conjecture (Lovász) | Graph Theory | Topological: Borsuk-Ulam |
| 15 | Five color theorem | Graph Theory | Induction on planar graphs |
| 16 | Sylvester-Gallai theorem | Geometry | Kelly's projective proof |
| 17 | Fundamental theorem of algebra | Analysis | Winding number / Liouville |
| 18 | Sperner's lemma | Combinatorics | Parity count on triangulation |
| 19 | Turán's theorem | Graph Theory | Zykov symmetrization |
| 20 | Pigeon-hole principle | Combinatorics | (Base case for combinatorial reasoning) |

Each of these should be given both an informal prose proof and a Lean 4 proof (or a
Mathlib pointer). The Lean references for most already exist in Mathlib4; the generation
task is writing the *illuminating informal layer*.

---

## 6. SFT FORMAT TEMPLATE

Each corpus entry should follow this schema:

```json
{
  "id": "elite_math_001",
  "domain": "number_theory",
  "difficulty": "undergraduate",
  "theorem": "There are infinitely many prime numbers.",
  "culture": "problem-solver",
  "elite_signature": "Euclid / Book",
  "proof_informal": "...<full informal proof with named steps, key insight, look back>...",
  "proof_lean4": "...<full Lean 4 code block, Mathlib imports explicit>...",
  "audit_score": 1.0,
  "lean_compiled": true,
  "criteria_passed": ["S1","S2","S3","S4","S5","I1","I2","I3","I4","C1","C2","C3","P1","P2","P3","P4"]
}
```

The `culture` field (Gowers: "problem-solver" | "theory-builder") and `elite_signature`
(which canonical name's style this example embodies) enable the model to learn that
*elegance is context-dependent*: Grothendieck's rising-sea style is elite for algebraic
geometry; Erdős's combinatorial trick is elite for graph theory.

---

*Sources: Aigner & Ziegler, Proofs from THE BOOK (Springer, 6th ed.); Hardy, A Mathematician's
Apology (1940); Pólya, How to Solve It (1945); Gowers, "The Two Cultures of Mathematics"
(2000); McLarty, "The Rising Sea: Grothendieck on Simplicity and Generality" (2003); Tao,
terrytao.wordpress.com/advice-on-writing-papers; Mathlib4 community, mathlib4 GitHub +
leanprover-community.github.io; Quanta Magazine, "In Search of God's Perfect Proofs" (2018).*
