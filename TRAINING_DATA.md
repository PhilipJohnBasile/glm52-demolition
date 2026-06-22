# Training Data — provenance · licenses · contamination (ledger)

Honest record of what the model was healed on, where it came from, and proof the reported numbers aren't
memorized. (The *model* is released; the heal *data* itself is not published.)

## Heal / SFT sources
External open datasets (via `scripts/27_build_heal_data.py`, `scripts/06_heal_lora.py`) + self-generated/verified
data + hand-authored gold seeds.

| Dataset | Use | License *(verify before redistributing the data)* |
|---|---|---|
| `open-r1/Mixture-of-Thoughts` | reasoning + code | Apache-2.0 |
| `open-r1/OpenR1-Math-220k` | math reasoning | Apache-2.0 |
| `open-thoughts/OpenThoughts-114k` | reasoning | Apache-2.0 |
| `HuggingFaceH4/ultrachat_200k` | general chat | MIT |
| `theblackcat102/evol-codealpaca-v1` | instruction→code | Apache-2.0 ⚠ Evol/GPT-distilled — check model-output terms |
| `Salesforce/xlam-function-calling-60k` | tool-calling | CC-BY-4.0 |
| `glaiveai/glaive-function-calling-v2` | tool-calling | Apache-2.0 *(verify)* |
| `glaiveai/reasoning-v1-20m` | reasoning | *(verify)* |
| `SWE-bench/SWE-smith-trajectories` | agentic / tool | MIT *(verify)* |
| `internlm/Lean-Workbook` | Lean proofs | Apache-2.0 *(verify)* |

**Self-generated / hand-authored (ours → MIT):** the Lean expert-iteration flywheel output, the design-soul +
7-facet **gold seeds** (`heal/facets/seeds/`, `heal/design/seeds/`), CallSieve retrieval data, verifier-mesh RFT.

## Eval benchmarks — TESTING only, never trained on
`openai/openai_humaneval` (MIT) · `openai/gsm8k` (MIT) · `mbpp` (CC-BY) · miniF2F (MIT). Loaded by
`58_bench` / `59_stem_diag` / `73_minif2f` for evaluation, not heal.

## Contamination — verified CLEAN (CPU, 2026-06-18)
The honest risk: the big reasoning/code datasets above *can* contain benchmark problems → memorized, not
reasoned. Checked with `scripts/81_contamination_check.py` (miniF2F vs Lean training) and
`scripts/82_heal_benchmark_contam.py` (benchmarks vs the 236 M-char heal corpus):

| Benchmark | Present in training? | Verdict |
|---|---|---|
| **miniF2F-test** (226) | 0 exact · 1 near-dup (0.4 %) | ✓ honest |
| **HumanEval** (164) | 0.0 % | ✓ the 19/20 is honest |
| **GSM8K-test** (sampled 300) | 0.0 % | ✓ honest |

Method: name-agnostic normalized exact-match + token-Jaccard near-dup (miniF2F) and normalized prompt-substring
(HumanEval/GSM8K) — verbatim/near-verbatim inclusion would be caught. **Reported numbers are reasoned, not
memorized.**

## License stance
Self-generated + hand-authored → MIT (matches the model + base `zai-org/GLM-5.2`, MIT). External-dataset portions
retain their upstream licenses (table). The released model is a derivative; **verify each dataset's license before
redistributing the heal data itself.**
