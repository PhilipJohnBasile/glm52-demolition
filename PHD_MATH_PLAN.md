# PhD-Math Plan — heal GLM-5.2 into a local Lean prover (tasks #27–31)

*Researched 2026-06-17. The lane where a demolished local model can genuinely do PhD-level math.*

## Strategic clarity: "PhD math" splits in two — only one is winnable
- **Informal research math (FrontierMath):** SOTA solves **<2%.** Even frontier models barely touch it.
  We cannot win here — nobody can, yet. *(Our GSM8K RFT confirmed: incremental informal-math gains are small.)*
- **Formal theorem proving (Lean 4):** where PhD-level math is *actually being cracked*, and it plays
  **directly to our verify-everything thesis** — every proof is machine-checked = correct-by-construction.
  **This is our lane.**

## The model to emulate: Goedel-Prover-V2 (Princeton)
SOTA with models **"80× smaller"** than competitors, high pass@N with *minimal* inference (unlike
DeepSeek-Prover-V2's two-model + huge sampling, or Kimina's test-time RL). Recipe = **our infrastructure:**
> expert-iteration + **verifier-guided self-correction using Lean feedback** + scaffolded data synthesis + model averaging

Simplifiers in our favor:
- **BFS-Prover:** simple **best-first search beats complex MCTS** — no fancy tree search needed.
- **DeepSeek-Prover-V2:** **subgoal decomposition** (theorem → lemmas → prove each).

**The realization:** "expert iteration" IS our **RFT/STaR loop** — generate → Lean-verify → keep correct →
SFT — pointed at Lean. We already built it for GSM8K (the 88%-solve run). We have `verify_lean`, the RFT
machinery (`65`), the Lean corpus seed (`68`). The prover recipe is our thesis, applied to math.

## The plan (ONE model, every proof checked)
| Phase | Task | What | Our infra |
|---|---|---|---|
| 1. Lean foundation | #27 | SFT on Lean 4 corpus (Lean-Workbook, mathlib, miniF2F-train, Goedel/DSP auto-formalized) | `68 --download` + `06_heal` |
| 2. Expert iteration ⭐ | #28 | generate → `verify_lean` → SFT on verified → repeat | `65_rft_math` retargeted + `verify_lean` |
| 3. Self-correction | #29 | failed proof → feed Lean error → revise → train on fixes | heal-from-error loop |
| 4. Test-time search | #30 | best-first search + subgoal decomposition, Lean-check, pass@N | new `66_prove.py` |
| 5. Benchmark | #31 | miniF2F-test, ProofNet, PutnamBench (pass@N, Lean-verified) | new eval harness |

## Honest scoping
- **Target:** NOT 88.9% miniF2F (massive compute). A healed GLM-5.2 specialist realistically reaches a
  **respectable miniF2F pass@N** — genuine **formal, PhD-adjacent math, fully local, every proof verified.**
- **Why local CAN compete:** the **Lean verifier does the correctness heavy-lifting** — the model only needs
  to search well. Goedel-Prover-V2 (80× smaller, SOTA) proves small/local wins in this one lane.
- **The differentiation:** a **local model whose every proof is machine-checked** — the purest expression
  of the verify-everything thesis. We don't claim FrontierMath; we claim *correct-by-construction* proofs.

## Start here
**Phase 1 + 2** — highest leverage, reuse what we have. Bulk the Lean corpus (`68 --download`), SFT, then run
Lean expert-iteration (the `65` loop retargeted). That alone yields a measurable miniF2F number and proves the lane.
Related: [[glm52-speed-findings]] (TurboQuant KV gives the context room for long proofs), task #26 (verifier-mesh
self-training — Lean is just another verifier in the mesh).

## Implementation specifics (deep research, 2026-06-17)
**🔑 Goedel-Prover-V2 is FULLY OPEN — adopt it directly, don't reinvent** (`github.com/Goedel-LM/Goedel-Prover-V2`,
[arxiv 2508.03613](https://arxiv.org/abs/2508.03613)): code + datasets + the iterative training recipe are all public.
Their **8B model hits 84.6% pass@32 on miniF2F — beating DeepSeek-Prover-V2-671B (80× larger)**; their 32B hits
88.1% → **90.4% after 2 self-correction rounds**. We stand on their shoulders, not from scratch.

**Datasets (HuggingFace, no auth):**
- `internlm/Lean-Workbook` — 57K main + 83K Plus ≈ **140K** (NL + formal stmt + proof), 93.5% acc.
- `Goedel-LM/Lean-workbook-proofs` — the **verified** proofs (parquet) → direct SFT data.
- `internlm/Lean-Github` — 28.6K theorems + 219K tactic steps from **real repos** (mixing real-repo proofs beats synthetic-only).
- LeanDojo Benchmark 4 — 122K theorems, 260K tactics, 168K premises from mathlib4.
- `miniF2F-lean4` (brando/ or HaimingW/) — **488 problems** (244 val + 244 test; AIME/IMO/AMC) = THE benchmark. ProofNet = undergrad.

**Toolchain (Phase 1, macOS):** `elan` (Lean version mgr) → `lake` project + mathlib4 → `lake exe cache get` (precompiled
cache). Wire `verify_lean` with **`LEAN_REPL=true`** (`lean_multi_attempt`, ~5× faster checking). `lean-lsp-mcp` (PyPI)
for agentic LSP interaction.

**Recipe (Phase 2, Goedel's 3 innovations):** (1) **scaffolded data synthesis** = a CURRICULUM of increasing difficulty;
(2) **verifier-guided self-correction** = revise from the Lean compiler (whole-proof, max ~30K tok + 2 correction rounds);
(3) **model averaging** = merge checkpoints to keep output diversity. Expert iteration throughout (Lean-verify → keep → SFT).
"One-shot SFT on high-quality synthetic traces lets even a ~7B model saturate Pass@1 on miniF2F" — so a compact model wins.

**ALGEBRA specifically (the easiest formal win):** mathlib's `ring` / `linarith` / `omega` tactics *crush* algebraic &
arithmetic goals, and Lean-Workbook is algebra-heavy. **REAL-Prover hit 56.7% pass@64 on algebra SFT-only.** Our informal
algebra (3/4, guessed) → **formal algebra via Lean, where the answer is PROVEN.** Likely the first domain to show a number.

## MLX-native execution (2026-06-17) — this would be the FIRST MLX formal prover
Research gap confirmed: **nobody has combined MLX + Lean theorem proving.** So this is NOVEL, and it matches our
"only 128 GB-fit GLM-5.2" uniqueness. The compute stack is **100% MLX / Apple Silicon** — we adopt only Goedel's
open **data + recipe** (the method), NOT their CUDA code.
- **Training / expert-iteration:** `06_heal_lora` = `mlx_lm.lora` → **auto-QLoRA** on our quantized 99 GB model
  (MLX switches to QLoRA automatically when weights are quantized). NOT Goedel's CUDA trainer. (Ref: 7B QLoRA on
  M2 Max ≈ 90 min / 5K examples — ours is bigger but hours-scale, feasible.)
- **Proof generation:** `mlx_lm.server` (MLX) — our existing serve path, with the prompt-cache (#25) for the loop.
- **Lean verification:** the Lean compiler runs on **CPU** (elan/lake); the MLX model runs on **GPU**; **unified
  memory = zero-copy**, so they coexist with no transfer overhead — the *exact* verified-decoding insight (model
  on GPU + verifier on CPU sharing RAM). `LEAN_REPL=true` for ~5× faster checks.
- **MLX-specific wins we already have:** the **M5 Max Neural Accelerators give ~3–4× on the proof-prompt PREFILL**
  (compute-bound — precisely what proof generation needs); **TurboQuant KV** gives the context budget for
  whole-proof generation (~30 K tokens); the verified-decoding unified-memory coexistence is purpose-built for this.
- **Optional:** Goedel-Prover-V2 weights convert to MLX via `mlx_lm.convert` — useful as a **teacher** for distillation
  or a baseline, but the goal stays OUR healed GLM-5.2 (one model, this model).

## Phase 2+ improvements — how to do the flywheel BETTER (researched 2026-06-17)
From Goedel-Prover-V2 ([2508.03613](https://arxiv.org/pdf/2508.03613)) + the 2026 expert-iteration literature —
the levers that take a basic verified-proof loop to SOTA (apply as Phase 2 matures):
1. **Scaffolded data synthesis (the #1 lever):** when a proof FAILS, use Lean's `extract_goal` to mine the
   FAILING SUBGOALS, convert them into easier focused tasks → an easy→hard CURRICULUM. Failures become
   training data, not waste — this is HOW Goedel scales from toy theorems to miniF2F.
2. **Save self-correction TRAJECTORIES:** `66_prove.py` already generates failed→Lean-error→fixed sequences —
   PERSIST the successful ones as SFT data → the model learns to self-correct NATIVELY (lifts pass@1 the most).
   We already generate them; just save them.
3. **Premise selection (LeanSearch v2, [2605.13137](https://arxiv.org/abs/2605.13137)):** RAG for proofs —
   retrieve relevant mathlib lemmas (nDCG@10 0.62) and inject into the prompt. Essential for harder theorems
   that need scattered lemmas (where our no-mathlib core-tactic set runs out).
4. **Tree search + beam-size decay** (vs our linear best-of-N): a proof-search tree, LLM proposes candidate
   tactics per node, beam decay balances explore/exploit per compute budget. Upgrades #30.
5. **Multi-round expert iteration:** "better models accept more data per round → sustained improvement, then
   saturation." Run several rounds; expect a curve that climbs then plateaus.
6. **Anti-forgetting:** mix 5–10% general data (we do this via `heal/lean-combined`). Confirmed best practice.

Goedel's full loop for reference: SFT (whole-proof + scaffolded) → RL (verifier feedback) → model averaging,
on a mix of scaffolded tasks + formalized NL math + expert-iteration proofs + self-correction trajectories.

## Breaking the plateau (researched 2026-06-17 — our flywheel saturated 2/5→4/5→4/5)
Plain expert iteration **plateaus after 1-2 rounds** (sparse positive rewards — confirmed, EvoCoT/STP). The
measured 4/5→4/5 round-2 flat is exactly this. The levers to push past it (in order of impact):
1. **Conjecture generation (STP, [2507.02726-style] self-play): the BIG lever.** A *conjecturer* role proposes
   NOVEL theorems "just beyond the prover's current ability" → an infinite fresh curriculum, not a fixed 20-set.
   Our `scaffold()` (decompose failures) is half of this; STP also *generates* new harder targets. Build a
   conjecturer mode in 67.
2. **Difficulty-aware self-evolving curriculum** (Self-Evolving Curriculum 2505.14970): feed the scaffold
   `curriculum.jsonl` forward + sample by difficulty (just-beyond-ability). We built the curriculum; wire it in.
3. **Diversity / entropy** ([2512.04359]): "policy entropy collapses early → premature saturation." Raise gen
   temperature + entropy regularization to keep exploring tactics (don't always sample the same proof).
4. **Failure-prefix conditioning** ([2601.20829]): recover saturated problems by conditioning on the *partial
   incorrect* trajectory — pairs with our saved self-correction trajectories. Targets the stuck `0+n=n` directly.
5. **Filter out easy proofs** (BFS-Prover): bias the training corpus toward the *harder* verified proofs, not all.
6. **⚠️ Don't over-iterate:** "prolonged self-training → reward hacking → model collapse." 2-4 rounds, then refresh
   data. Our 2-round stop was correct.

## ⭐ NOVEL plateau-breaker (built + TESTED 2026-06-17): tactic-enumeration cold-start bootstrap
The 4/5 ceiling is a COLD-START: expert-iteration can only train on proofs the model first produces, but it
never once solves 0+n=n (keeps trying rfl; needs omega/simp) → no verified proof → nothing to compound. THE FIX
(66_prove.enumerate_tactics): when the model fails, brute-force CORE_TACTICS [rfl, omega, decide, simp, norm_num,
tauto, simp_all, trivial, aesop, induction…] via Lean (CPU, no model) → the first that verifies is a real proof.
TESTED 5/5 incl. the stuck 0+n=n → `by omega` and and_comm → `by simp_all`. Wired into 67 gen (enumerate_fallback
=True) so the flywheel's TRAINING data now includes the bootstrapped proofs → the model LEARNS the tactic it
couldn't discover → breaks the plateau HONESTLY (eval keeps enumerate_fallback=False, so the model's real score
isn't inflated — after training it should solve 0+n=n itself). This is BFS-Prover's tactic-enumeration insight
applied as a cold-start seeder. Next flywheel run (with the fix) is the honest test: does pass@1 reach 5/5?
