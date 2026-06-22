> ⚠️ **Describes an earlier version (v1: 3-bit / 99 GB).** Current = **v3: 4-bit / ~98 GB, HumanEval-164 = 69%, now PUBLIC** (https://huggingface.co/philipjohnbasile/GLM-5.2-Demolition-q4a4-soul-MLX, MIT). Canonical truth: `MODEL_CARD_v3.md` + `MISSION_SUMMARY.md`.

# Benchmarks — frontier vs us (honest), and how high we can realistically punch

Frontier = Claude Opus 4.8 / Mythos, GPT-5.5/5.6, Gemini 3.1 (June 2026). **Us** = GLM-5.2-Demolition q3a4
(77/256 experts, 3-bit, 99 GB, local on one Mac). Projections are **honest + conservative** — the thesis is
"out-VERIFY where verification is possible," so the ceiling is HIGH on verifiable tasks and LOW on open-ended ones.

## The list (★ = our positioning's core benchmarks)

| Benchmark | Type | Frontier 2026 | Us NOW | Us TUNED (honest) | Why that ceiling |
|---|---|---|---|---|---|
| ★ **SWE-bench Verified** | agentic SWE | **~88%** (Opus 4.8 88.6, GPT-5.5 88.7) | not run (harness #62 built) | **20–35%** | raw-capability capped; agent+verify helps but can't reach 88 |
| ★ **SWE-bench Pro** (contam-resistant) | agentic SWE | ~80% (Fable 5) / 64% (Opus 4.7) | not run | **15–25%** | hardest; our contamination-honesty is the edge, not the score |
| ★ **Terminal-Bench** | agentic shell | ~80% | not run | **15–30%** | scaffold-dependent; our defense layers help reliability |
| ★ **Aider Polyglot** | code-edit (6 langs) | ~80–90% | not run | **35–55%** | well-specified edits + best-of-N close more of the gap |
| **HumanEval** | code (saturated) | ~93% | **95%** (19/20, n=20, contam-clean) | **85–92%** (HumanEval-164) | verifiable → best-of-N+tests punch near-frontier |
| **MBPP** | code (saturated) | ~92% | not run | **80–90%** | verifiable, well-specified |
| **LiveCodeBench** | competitive prog | ~83% (Qwen3.5) | not run | **25–45%** | hard novel problems; capability-capped |
| **BigCodeBench** | realistic code | ~55–60% | not run | **30–45%** | verifiable but complex |
| ★ **our SQL / design / Lean gates** | verified-domain | n/a (we invented these) | **strong** | **strong** | structural advantage nobody else ships |
| **GSM8K** | grade math (sat.) | ~96% | **67%** (8/12, n=12) | **82–92%** | SymPy-verified + best-of-N |
| **MATH** | hard math | ~95% | not run | **45–65%** | capability-capped on the hardest tiers |
| **AIME** | olympiad math | ~85% | not run | **15–35%** | very hard; demolition hurts most here |
| ★ **miniF2F** (formal) | Lean proof | specialized ~73% | **~14%** (running) | **25–45%** | local Lean prover + expert-iteration + heal |
| **GPQA Diamond** | grad science | ~91–94% | not run | **35–50%** | broad knowledge; demolition + 3-bit hurts |
| **MMLU** | knowledge (sat.) | ~90% | not run | **65–78%** | knowledge-capped by pruning |
| **HLE** (Humanity's Last Exam) | frontier-hard | ~64% | not run | **<10%** | honestly out of reach for a demolition |

## The honest pattern (this is the whole strategy)
- **VERIFIABLE + well-specified → we punch HIGH** (HumanEval/MBPP/SQL/GSM8K/Aider/formal-proofs): real verification
  + best-of-N closes most of the capability gap. This is the *only* lane the "beat-frontier-in-niche" thesis survives.
- **OPEN-ENDED + hard-reasoning → we're CAPPED well below frontier** (HLE/GPQA/AIME/LiveCodeBench/hard-SWE): the
  3-bit demolition's raw ceiling can't be tuned away. No honest projection reaches frontier here.

## Where "tuning" actually moves the needle (in priority order)
1. **Best-of-N + verification at serve time** (already built) — the biggest lever on every verifiable benchmark.
2. **The heal** (#17 design + the soul corpus) + **facet-balanced re-prune** (#23) — recover what pruning cost.
3. **Lean prover loop** (#30) for miniF2F; **SymPy gate** for GSM8K/MATH.
4. **Dynamic quant** (#59) + **better calib** (#61) — recover quality at the same size.
5. Run the real benchmarks (#62 SWE-bench, full HumanEval-164) to replace estimates with measured numbers.

**Bottom line:** we can credibly land **near-frontier on the verifiable lane** and should claim *only* that —
and we stay honestly far behind on open-ended reasoning. The win condition is "verified + local + private + tunable,"
never "smarter."

## Queued as tasks (the full suite is now on the list)
| Task | Benchmark(s) | Lane |
|---|---|---|
| #31 | miniF2F (running) | verifiable ✅ |
| #62 | SWE-bench Verified | agentic ★ |
| #63 | HumanEval-164 + MBPP | verifiable ✅ |
| #64 | Aider Polyglot | agentic ★ |
| #65 | GSM8K-full + MATH | verifiable/capped |
| #66 | LiveCodeBench | capped (honest ceiling) |
| #67 | GPQA Diamond + MMLU | capped (honest ceiling) |

Run order: finish miniF2F (baseline) → run the verifiable ones WITH the +loop → deep-tune (heal/re-prune/dynamic-quant)
→ re-run for the delta. Each: contamination-checked (81/82) + official harness where one exists. Publish the CAPPED
numbers (GPQA/LiveCodeBench) next to the strong ones — that honesty is the differentiator.
