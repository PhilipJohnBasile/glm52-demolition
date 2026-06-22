# Head-to-Head Research Log — Our Corner's Losses, Root Causes & Fixes (#111)

**Cycle:** lose → 10× research → log → fix → re-fight until WIN → next bug.
**Contestants:** ours (`57_tool_agent` + soul2, 3-bit demolished GLM-5.2, local, $0) vs **claude / codex / agy** (frontier cloud agents).
**Task:** injected callsieve mutations (Rust), scored by `cargo test` exit code. Cloud baseline: **18/18 = 100%** (codex ~102s, claude/agy ~210s).

---

## Round 1 — LOSS (validation: `heuristic` `div_ceil(4)`→`/4`)
- **Result:** 0/1 · 163 s · FAILED.
- **Trace:** `⚠️ stopped in 20 steps`; tools used = ls,ls,read_file,peek,grep,grep_ptr×… — **0 edit calls.** Burned the entire budget exploring, never reached an edit.
- **Root cause:** default `--max-steps=20` is too low for a slow 3-bit model that over-explores. The cloud agents run with far larger internal step budgets → the cap was an unfair handicap.
- **FIX:** `--max-steps` 20 → 50 (level the budget). Pulled the rigged 0/1 off the board.

## Round 2 — LOSS (re-fight, 50 steps, same bug)
- **Result:** HUNG ~8 min · 0 edits · agent at **0% CPU (blocked on serve)** · serve KV ballooned to **~109 GB** (RAM 15% free).
- **Root cause:** **3-bit Computation Collapse** — a long generation degenerates into a non-terminating runaway; the agent never receives a usable response. Documented limit in `dist/MODEL_CARD.md` / `AGENTIC.md`. serve_stable's 115 GB guard held (no kernel panic) but the turn never completed.
- **FIX:** route ours through the **concise-thinking proxy** (`08_think_proxy.py` :8081 → :8080) which caps reasoning tokens → prevents the runaway. Restart serve fresh to clear the bloated KV. (Same generic task prompt as the cloud agents — no gaming.)

## Round 3 — think-proxy re-fight: ABORTED (proxy failed to bind :8081) — superseded by a bigger finding ↓

## 🔑 ARENA-BIAS FINDING (user-prompted: "is callsieve helping or hurting?")
**callsieve was HURTING the comparison three ways:**
1. **Home-field for cloud:** `callsieve` is ON PATH + ships a `CLAUDE.md` ordering agents to run `callsieve agent-context` first → claude/codex/agy (which read CLAUDE.md) get callsieve's own zero-token retrieval to pinpoint the bug. The arena is *literally a claude-assist tool.*
2. **Navigation tax for ours:** the 57-agent ignores CLAUDE.md → hand-navigates 29 files / 387 tests with grep/peek (fumbled onto CODE_OF_CONDUCT.md).
3. **Collapse trigger:** callsieve's large context → long prompt → the 3-bit runaway (= Round 2's collapse).
**FIX:** switch to a NEUTRAL minimal arena (`/tmp/neutral_arena`: 1 file, no CLAUDE.md, `round_up_div` ceil-div bug + test). Removes the home-field, the navigation tax, AND the collapse trigger in one move. NOTE: cloud's 18/18 on callsieve is *flattered* by home-field; a fair cloud baseline must be re-run on the neutral arena too.

## Round 4 — ours on neutral arena: ABORTED (serve had timed out — a zombie process held :8080, `Errno 48 Address already in use`; clean-killed by port + restarted).

## 🔄 FAIR-FIGHT RESTART — the real framing (user: "callsieve is OURS — use it on ours only; cloud + local can suck it")
The callsieve-arena "bias" is resolved *in our favor, legitimately*: callsieve is our product (#6), so the honest fight is **OUR FULL STACK vs theirs**, not a stripped model.
**New rules (clean Round 1):**
- **Arena = callsieve** (the real repo — our home turf).
- **OURS:** `run_contestant` pre-runs `callsieve agent-context <wt> <task>` → injects the zero-token focused pointer into the prompt. VERIFIED: pinpoints file+symbol+line (e.g. `src/query/tokens.rs` / `heuristic`:111) with `retrieval_model_tokens=0`. Bonus: the short focused context should dodge the 3-bit collapse.
- **CLOUD / other-local:** `CLAUDE.md` + `.mcp.json` + `mcp-server.json` removed from their worktree per-bug → they navigate blind with their own tools. They don't get our weapon because it isn't theirs.
- Old board (cloud 18/18 on home-field callsieve) archived as biased.
**The thesis under test:** model-alone, ours loses (3-bit collapse + over-exploration, Rounds 1–2). The real product is **model + callsieve + verifiers** — does THAT beat the frontier agents fighting blind? Round 1 (fair) re-running now.

## 🔒 Round (fair, shim-enforced) — callsieve is OURS-ONLY at the OS level
- Deny-shim `/tmp/nocallsieve/callsieve` (exit 127) prepended to cloud/local PATH → their `callsieve` = "command not found"; `claude`/`codex`/`agy` still resolve; ours keeps the real binary. Verified.
- **D3 finding (ours+callsieve, small file tokens.rs):** hint landed (856 ch); ours made **1 edit** (vs 0 in Rounds 1–2 — callsieve broke the "won't try" failure) BUT the edit was wrong (line112 stayed `/4`, 2 tests fail), stopped at 15 steps. NEW bottleneck = **edit quality** (3-bit picks wrong fix), not navigation/collapse. Next fix target.

## ⚠️ CORRECTION — real bottleneck (D3 full trace)
"1 edit" was a mis-count → **0 real edits**. Trace: steps 6-13 = `cat tokens.rs` ×6, stall-detector ABORTED at step 14. Ours saw the file + the callsieve hint (landed, 856ch) but **looped on read/cat, never committed to an edit** — a 3-bit *decisiveness* failure, NOT callsieve/navigation. callsieve is NOT hurting (hint landed; ours stalled on its own).
**FIX (user A/B): each round run ours-armed (callsieve) vs ours-bare (none) on the same bug → measure callsieve's net effect. Dropped mcp.rs (1700-line collapse-trap); pool = tokens/classify/skeleton (focused).**

## Round (win-probe, heuristic + callsieve + workflow-nudge) — LOSS
- line112 stayed `/4`; **0 edits**; trace = `grep_ptr('pub fn count')` repeated 6× (steps 10-18), stall-ABORT at 19. The workflow-nudge ("read once→edit→verify") did NOT help.
- **Root cause: REPETITION DEGENERATION** — the 3-bit model emits the identical tool call over and over (greedy/low-temp collapse in the action space), never reaching `edit_file`. Not a navigation/prompt issue.
- **NEXT FIX: sampling — add repetition_penalty (~1.1-1.3) + temperature ~0.6 to the agent's serve requests to break the loop.**

## Round (win-probe v2, rep-penalty 1.15 + temp 0.6) — LOSS
- Still 0 edits; spread = 6× grep_ptr('fn|test')→same 'fn as_u8', stall-ABORT. line112 stayed /4.
- **WHY rep-penalty failed: the repetition is CROSS-TURN** (model re-emits the identical tool call across separate generations); repetition_penalty only acts WITHIN one generation. Wrong lever.
- Also: grep_ptr returns only the FIRST match (`as_u8`), never the `heuristic` fn the callsieve hint named → the model loops hoping for a different result.
- **NEXT FIX: strengthen the scaffold stall-handler — on a repeated read/grep, BLOCK it and inject a forceful directive: "STOP reading. CallSieve gave you the location. Call edit_file NOW with the fix." (force progress instead of nudging).**

## Round (win-probe v3, force-edit) — INVALID (serve crash, not a fair test)
FORCING_fired=0, 0 step lines, RAM→95% free = the 99GB serve UNLOADED mid-probe (crashed under 14% RAM pressure). The agent had no serve to call → hung till cap. The force-edit fix was never actually exercised. SEPARATE FINDING: serve_stable crashes under long agentic KV growth even with the 115GB guard. Retry v4 with MLX_MEM_GB=110 (more headroom) + step-count logging.

## 🏁 DEFINITIVE VERDICT — it's the BITS (the model), NOT the scaffold
Control: SAME 57-agent (parser-fixed to accept standard fn-calling args), SAME heuristic bug, SAME callsieve hint, only the model swapped.
- **Qwen (qwen3-coder-next, 4-bit via LM Studio :1234): edits=2, toolerr=0 → line112=div_ceil(4) → `test result: ok, 145 passed`. WON.**
- **ours (soul2, 3-bit GLM): edits=0, loops on grep_ptr, 0 commits → FAILS** (across 6 probes).
CONCLUSION: scaffold is sound (Qwen proves it). Ours's failure = the 3-bit quantization (and/or heal) destroyed agentic decisiveness — reasons about the bug, won't commit the edit.
CURE (both already built): (1) #59 saliency-dynamic 4-bit re-quant — the real fix, keep decision-critical layers at 4-bit within 128GB; (2) #82 best-of-N — 4-8 parallel attempts, take any pass (tonight-able stopgap).
BONUS: the parser fix makes the 57-agent multi-model → Qwen is now a real local rival for the head-to-head (ours vs Qwen vs cloud, all through our scaffold).

## Re-quant v6 (saliency-dynamic 4-bit) — DID NOT CURE the loop
v6 (125 expert mods @3-bit, salient/early/late @4-bit; 111GB) loops on `peek` 13× exactly like v4, 0 edits, ignores FORCING. So it's NOT the bits. Qwen-control said "our model" → narrows to HEAL (soul adapter) or PRUNE. Also: v6=111GB is too big to serve reliably on 128GB; v4=99GB is the serving sweet spot. NEXT: serve v4 BARE (no soul adapter) → if it edits, the heal is the culprit (easy fix); if it loops, it's the prune/base.

## CLEAN read-fix test (warm serve, read_file→12000) — REFUTED the blindness theory
Serve confirmed generating (content gate "OK"). Ours called read_file ONCE (full 12000-char file, line112 included) then looped peek(start=0) ×10, ABORT, 0 edits. It HAD the code and wouldn't commit. So NOT read-truncation. (My earlier 'serve hung' verdicts were a grep bug: model returns output in a 'reasoning' field unless enable_thinking=false; the serve worked all along.) NET: ours genuinely won't emit an edit — consistent across bits(v6)/heal(bare)/read-fix/warm-serve. Final test: inject exact code + exact change into the prompt → can it edit AT ALL when handed the fix?

## 🏁🏁 RESOLVED — OURS CAN EDIT. The wall was NAVIGATION, not the model.
INJECT test (exact line + change in prompt): ours called apply_patch(old→new), ran cargo test (ok, 145 passed), done — 3 CLEAN steps. So the edit mechanism works perfectly. The ENTIRE night's "loop" = ours can't NAVIGATE to the bug (loops peek hunting the line); once the code is in front of it, it fixes in 3 steps. Qwen won by navigating (cat/git) then editing; ours navigates poorly but edits fine. CURE = callsieve injects the CODE SNIPPET (not just the file/line pointer) → ours sees bug → apply_patch → win. This is the ours+callsieve synergy, proven. Full chain eliminated: NOT bits/heal/prune/read-trunc/serve/edit-mechanism → NAVIGATION, which callsieve solves.

## Cure refinement: SHORT pointer beats full snippet (3-bit collapses on long context)
SNIP2: serve gen-probe OK, but agent hung 0 steps on the snippet prompt. INJECT (won) used a SHORT precise prompt; snippet tests stuff the full code block → longer context → 3-bit collapse on first call (the night's recurring failure mode). CURE = callsieve gives a SHORT pointer 'bug at file:line: <the one buggy line>' (NOT the full snippet) → short context, no collapse, ours edits. Testing /tmp/SHORT.log.

## 🏆🏆🏆 CURED & PROVEN (04:59) — OURS IS A WORKING AGENTIC CODER
CURE test (lenient apply_patch + short pointer + warm serve): ours read_file→grep_ptr→found bug→apply_patch('text.len()/4'→'(text.len()+3)/4', landed via LINE-MATCH FALLBACK)→cargo test exit=0→done. 8 steps, self-driven, RESULT ok 145 passed. THE REAL ROOT CAUSE was apply_patch requiring exact+unique `old` match — the model padded `old` with a guessed comment line → 0 matches → rejected 6×. FIX: src/dev_tools.py apply_patch falls back to matching the LAST non-blank line of old/new (the actual change) when the padded context misses.
FINAL TALLY — ours was buried under 5 SCAFFOLD bugs, ZERO model bugs: (1) greedy temp 0.2→0.6+rep_penalty; (2) read_file 4000<line112→12000; (3) gen-probe must set enable_thinking=false (else output hides in 'reasoning' field → false 'serve hung'); (4) 3-bit collapses on long context → keep callsieve hints SHORT (one-line pointer, not code dump); (5) apply_patch too strict → line-match fallback. The Qwen control was right (scaffold, not bits) but the deeper truth: OUR scaffold had paper-cuts that only bit a quantized model. SHIPPED: callsieve OS-shim, multi-model arg-parser, read_file 12000, sampling fix, apply_patch fallback. MORNING: wire short-pointer into headtohead callsieve-arming + re-run the A/B fight (cloud baseline claude/codex 6/6, agy 0/6) → ours should now post real wins.

## Morning: the A/B-automation gap is callsieve LOCALIZATION (#6), not the model
Wired a callsieve-pointer into headtohead ours-arming. The AUTO pointer is unreliable for random mutations: callsieve's symbol-ranking, given a generic failing-test query, drifts to `mod tests` or the wrong source fn. Tried 3 query strategies — (a) raw task, (b) "source not tests", (c) failing-test first-token — each MISSED the mutated line for the div_ceil bug (picked mod tests @101, count @95, default @152). This is callsieve retrieval-quality (#6), separate from the model.
BUT the A/B SIGNAL is already proven in controlled tests: ours-ARMED (accurate short pointer: CURE/INJECT) → PASS, cargo test ok 145; ours-BARE (no pointer: CLEAN/SIGHTED) → peek-loop, fail. So callsieve's advantage is real; scaling it through the auto-harness needs callsieve bug-localization. NEXT (one of): (a) tune callsieve symbol-ranking to surface the source fn whose body changed; (b) let the 57-agent call callsieve as a TOOL directly (now read-cap+collapse+patch are fixed) instead of pre-injecting a parsed snippet — the truer "ours+callsieve product". DID NOT fabricate an auto-harness win-rate.

## Callsieve localization FIXED (the #6 gap) — focus = source, never `mod tests`
Root cause: for a bug-localization query ("a test in X is failing"), callsieve's per-file symbol focus surfaced the inline `#[cfg(test)] mod tests` block instead of the implementation it exercises — sending the agent into the test, not the source. Fix in src/query/mod.rs (build_context_with read-first construction):
  1. `test_symbol_flags()` — flags test scaffolding: a test module, `test`-kind, `test_*`, or any symbol whose line-range is inside a `mod tests` block (catches inner test fns with arbitrary names). Key subtlety: the indexer's module kind is the string "module" (NOT the compact "mod" display form) — matching "mod" was a silent no-op.
  2. demote test symbols below source in the focus ordering, regardless of query wording (a "test failing" query is a SOURCE-bug request; tests stay reachable via the related-tests channel + lower sy entries).
  3. `enrich_test_only_file()` — when a file is surfaced ONLY via tests, pull its source symbols from the index (ranked by query affinity + a boost for names embedded in the file's test names) so there's an implementation to focus on.
VERIFIED: agent-context on tokens.rs `.div_ceil(4)→/4` now puts `heuristic` (the exact buggy fn, snippet contains the bug) at sy[0]; skeleton/classify point at source (not tests). Genuine test-intent queries still surface tests. New regression test `inline_test_module_is_not_a_source_files_focus_symbol`; full suite 206+145 pass, clean build/clippy. Exact-fn pinpointing for arbitrary mutations still needs the failing-test name in the query (caller supplies it) — but callsieve no longer mis-aims at the test.

## Callsieve PINPOINT fix (follow-up) — focus the SOURCE the failing test exercises
The first fix put focus on source but the EXACT function needed the test name in the query, and even then it landed on the test fn (the matched set didn't include the `mod tests` symbol, so its range wasn't computed → the inner test fn wasn't recognized as scaffolding). Refactor: `test_module_ranges()` now computes `mod tests` line ranges from the file's FULL symbol list; `is_test_symbol(sym, ranges)` flags against those. So a query carrying the failing test name `heuristic_is_bytes_over_four_rounded_up` is recognized as a test, demoted, and `enrich_test_only_file` surfaces source `heuristic` (ranked by affinity + test-name token linkage) as the focus. VERIFIED: all three — generic "a test is failing", bare test name, and file+test name — now return sy[0]=['heuristic',111] (the exact buggy fn). Regression test extended (pinpoint-by-test-name); full suite 206+145 pass, clean build+clippy.

## Callsieve call-graph linkage (3rd fix) + honest ceiling
Added: when a file is surfaced only via tests, boost source symbols that the matched (failing) test actually CALLS (lookup.references_from_symbol -> target_symbol_id), via the indexed call graph — a direct test->implementation edge, robust to noisy test names (+20 vs +5 for name-token linkage). 
WHAT CALLSIEVE NOW DOES (verified): (a) never focuses `mod tests` — always source; (b) pinpoints the buggy fn when the query names the specific test, the function, OR is generic on a single-candidate file (all three → sy[0]=heuristic@111, snippet contains the bug); test-intent queries still get tests. 206+145 tests pass, clean build+clippy.
HONEST CEILING: a single failing test that exercises MANY functions (e.g. `default_active_is_heuristic_and_max`) calls active+heuristic+max — callsieve surfaces all its callees but cannot know WHICH holds the bug from the test name; that needs the failed ASSERTION (expected-vs-actual), which is not a callsieve input. Integration-side follow-up (headtohead/agent): pass the MOST SPECIFIC failing test (or the assertion line), not just the first one cargo reports — then callsieve pinpoints.

## Code review of the callsieve fix — caught + fixed a self-inflicted regression
Adversarial review of my own diff found: unconditional test-demotion REGRESSED genuine test-browse queries ("show me the tests for X" focused source, and with MAX_SKIM_SYMBOLS_PER_FILE=1 the test was dropped from the compact sy entirely). Existing suite didn't catch it. FIX: added ranker::has_bug_intent + prefers_implementation_focus (= has_bug_intent || !has_test_intent); gate enrichment + demotion on it. "a test is failing"→demote (bug intent); "show me the tests"→keep test. Added test-browse regression assertion. Other review notes (accepted/minor): magic weights 20/5 not named consts; test-detection is Rust-centric (mod tests + test_ prefix, doesn't read #[test] attr — misses bare #[test] fns outside a mod; non-Rust inline tests rely on file.is_test); enrichment can surface a const over a fn (no kind preference). 206+145 pass, clean build+clippy.

## Review follow-ups fixed + CEILING RAISED
All review minors fixed: (1) magic weights -> named consts CHANGED_SYMBOL_BOOST/TEST_CALL_EDGE_BOOST/TEST_NAME_LINK_BOOST; (2) Rust-centric detection -> indexer now marks bare `#[test]`/`#[cfg(test)]`/`#[bench]` fns (outside `mod tests`) as kind "test" (mark_rust_test_functions in symbols.rs, both tree-sitter + fallback paths; only 1 unrelated kind=="function" check in repo, low risk); (3) enrichment prefers callable kinds (fn over const) on ties.
CEILING RAISED (the multi-callee failing test): build_context now runs `git diff -U0 HEAD` for bug-intent queries (ranker::has_bug_intent) and boosts source symbols whose body overlaps the working-tree diff (CHANGED_SYMBOL_BOOST=100, the top signal). So `default_active_is_heuristic_and_max is failing` (a test exercising 3 fns) now focuses `heuristic` — the CHANGED function — instead of the first callee. Graceful no-op for non-git repos/clean trees (verified, no crash). 3 new regression tests (changed_function_is_focused…, bare_test_attribute…, + the earlier inline/pinpoint/browse). Suite 208+145 pass, clean build+clippy.

## 🎉 #113 VALIDATED — line-level best-of-N + fix-packet++ cracks BOTH bug classes (2026-06-21)
The harness-vs-standalone gap was MODEL SAMPLING VARIANCE (3-bit temp 0.6 sometimes emits invalid Rust like `if false else`, hallucinated comment formats) + agent escape hatches (clarify/peek-loop/garbage-patch). Fix = bypass the wandering ReAct loop for LOCALIZED bugs: scripts/bestofn_fix.py generates N candidate replacement lines directly, compile+test-gates each, applies the FIRST that passes. RESULTS: div_ceil (disclosable/variance) PASS in 1 candidate `(text.len()+3)/4`; skeleton >/< (subtle operator-flip) PASS in 3 candidates `if end > header_line` — but ONLY with fix-packet++ (the failing test's ASSERTION BODY in the hint, not just the name — the name doesn't disclose flip direction, the assertion does). bestofn_fix.py now auto-extracts failing-test bodies (self-contained). NEXT: wire into headtohead.py ours-armed (callsieve localizes the line → bestofn_fix), re-run A/B to confirm in-harness pass-rate. Metric: candidates-to-fix (1 disclosable, ~3 subtle).

## 🔧 5 scaffold fixes (2026-06-21) — ours can't NAVIGATE/EDIT was all scaffold, model is capable
Found by re-running the full agent on div_ceil and reading every step:
1. **done-gate** (integrity.py): `_FAIL` matched "0 failed" in cargo's PASS line → `done_has_proof`=False → a PASSING agent's `done` rejected → it kept editing and BROKE its own green fix. Fixed: precise `_FAIL` (exit=[1-9] | "N failed" N≥1 | rustc error[E#] | panic | traceback), not bare \bfail.
2. **apply_patch self-correct** (dev_tools.py): on mismatch, show the ACTUAL code at the target so the model stops re-emitting a doomed `old` (it was repeating an identical broken patch 9×).
3. **clarify→proceed** (57_tool_agent.py): clarify was an escape hatch ("ASK THE USER") even when the model KNEW the fix → now "no user, state your assumption and PROCEED; the test verifies".
4. **read_file peek-loop** (57_tool_agent.py): read_file caps at 12000 chars BUT every obs went through ptr_store.maybe_store (THRESHOLD~2000) → 6KB file became a HANDLE → forced peek → model loops re-peeking a STALE handle id (read_file:4 vs live :5) → ∞. The night's read_file→12000 fix was silently undone by ptr-ization. Fixed: read_file bypasses maybe_store (it's already capped + the agent asked to see it).
5. **apply_patch matcher** (dev_tools.py, Aider-informed): old fallback anchored on `ol[-1]` (LAST line, often `}`, not unique → failed). New: find the single CHANGED line (in old∖new) + its replacement (new∖old), edit JUST it — position-independent + WHITESPACE-FLEXIBLE (Aider's lesson: quantized models mis-indent constantly). Unit-tested: exact / last-line-is-brace / mis-indented all pass.

RESEARCH (Aider edit-format): search/replace is the RIGHT format (vs line-number/unified-diff) ✅ we use it. BUT quantized models have a real edit-error drop — Aider bench BF16 71.4% → q4 53.4% (~18pt). So mis-edits are EXPECTED for our 3-bit model → best-of-N + verifier (#113, validated) is the ESSENTIAL mitigation, not optional. ws-flexible matching + changed-line anchor recover many of those mis-edits cheaply.

## 🔬 10× RESEARCH SWEEP (2026-06-21) — arXiv + HF + GitHub + Reddit, deep-read. Re-ranks the levers by EVIDENCE.

### #114 QAD heal → RECOVER-LoRA recipe (arXiv 2606.04238, Jun 2026) — DATA-FREE, validated at 3-bit. THE accuracy lever.
Concrete recipe: (1) keep the quant; (2) train LoRA ONLY on the most-degraded layers (paper: gate/up proj) via **KL-logit distillation** from the FP teacher (we HAVE the BF16 original on disk). (3) **DATA-FREE synthetic data**: model generates first 3-5 tokens deterministically then stochastic to max-len, 10k samples — "synthetic ≈ curated labeled data". LoRA rank 32, alpha 64, lr 1e-4, **Kaiming init (NOT OLoRA — degrades on quant)**. Objective: min KL(softmax(teacher)||softmax(student)). Results: 2-bit 9/12 benches 80-95% recovery; 3-bit milder (less to recover). Also NVIDIA QAD (2601.20088): robust to data, works for SFT+RL+merge pipelines where QAT fails. BitDistiller: fwd+rev KL self-distill. → #114 is now a CONCRETE, low-risk, data-free GPU job. Biggest accuracy lever with a proven recipe.

### #113 best-of-N → FUNCTION-level repair + verifier is PROVABLY optimal.
Fault-localization granularity (arXiv 2604.00167, Qwen3-Coder-30B on SWE-Bench-Mini): line 43.6% / **function 45.6% (best, lowest variance)** / file 42.6%. "Perfect FL ≠ good repair" (45.6% even with ground-truth loc). Instance-dependent. → UPGRADE bestofn_fix: keep line-level (cracks operator-flips in 1 cand) but ADD a FUNCTION-level fallback (regenerate the whole fn) for multi-line bugs — callsieve already gives the function. Theory: "Scaling TTC WITHOUT verification is suboptimal" (2502.12118) proves a √H verifier gap → our verifier-gated best-of-N is provably better than verifier-free. VG-Search (2505.11730): +3.6% over best-of-N at -52% FLOPs (efficiency). Scaling Agentic Verifier (2602.04254): GENERATE extra model test-cases to strengthen execution-verification. CONTEXT: 45.6% is the SWE-bench ceiling even with ground-truth — our injected-mutation task is far easier (we pass them), so our numbers are honest-but-easier than SWE-bench.

### #110 MoE-Sieve → ROUTING-GUIDED saliency beats weight-norm.
Our sieve used ‖A‖·‖B‖ (weight magnitude). SOTA uses ROUTING saliency: REAP (CerebrasResearch/reap, GitHub) = router gate-value × activation-norm, "big advantage at 50% compression"; DR-LoRA = routing-freq + gradient-rank; MoE-Sieve paper (2603.24044) = routing-guided LoRA, 70-73% param cut ≈ full LoRA; ConMoE = unlabeled-calib routing stats, no fine-tune. → UPGRADE #110 metric to router-gate×activation-norm (needs a calibration forward pass). Our 49% (weight-norm) is a floor; routing-guided should keep MORE quality at the SAME size, or hit 500MB safely.

### MLX M5 Max enhancements (user ask): MLX v0.30.0 = M5 Neural-Accelerator support (macOS≥26.2; we're macOS 27). **INT8 is the M5-NA fast path: ~2× throughput over FP16 for 8-bit integer matmul** (NA = per-GPU-core matmul units, Tensor-Core-like, unified-memory-coupled). 4× TTFT prefill + 3.8× FLUX vs M4, automatic. → IMPLICATION: prefer INT8 where possible; #117 TurboQuant KV with k_bits=8 hits the NA 2× path. Verify MLX≥0.30 installed (BACKLOG says 0.31.2).

### #115/#69 EAGLE-3 on MoE = MARGINAL (honest deprioritize). mlx-lm Discussion #890 EAGLE-3 MLX prototype: 34% acceptance → 1.34 tok/step → ~1.05× on the hard case; dense models get 3.75× (ALU-bound) but MoE spec is weak (expert-routing, matches our "MTP measured-dead on MoE"). Tree-attention blocked by single-offset RoPE KVCache. → keep #115/#69 LOW priority; the decode win isn't here.

### Local rivals to beat (#111): Qwen3-Coder-30B-A3B-MLX is THE local pick June-2026 (~30-35 tok/s M4 Pro, Q4_K_M ~17GB); also DeepSeek-V4, Kimi-K2.6. MLX ~15-25% faster than GGUF. Get these via `lms get --mlx` for the same-scaffold model-only axis.

### EVIDENCE RE-RANK of the roadmap: #114 Recover-LoRA (concrete+data-free, biggest accuracy) > #113 function-level refine (cheap) > #110 routing-saliency (better metric) > #117 INT8-KV on M5-NA > #115 EAGLE (marginal on MoE, deprioritize).

## ⚠️ OBSOLETE: the logged A/B (ours-armed 0/4, ours-bare 0/2) is PRE-FIX — DO NOT CITE.
It ran the OLD full-agent armed path BEFORE today's 6 scaffold fixes (done-gate/peek-loop/clarify/apply_patch/ws-flex) and BEFORE bestofn_fix wiring. Both arms wandered to ~800-920s and failed everything incl. the easy div_ceil — it measured the broken scaffold, not callsieve's value. The valid head-to-head (armed-via-bestofn vs bare, fixed scaffold) is PENDING (after #114). Standalone bestofn = 3/4.

## 🔧 #114 SFT divergence — root cause + fixed recipe (2026-06-21, "research first, check twice, code once")
v1 diverged: loss 0.028 (iter30) → 17.25 (iter100). ROOT: lr 1e-4 × scale 20 × HARDCODED warmup:100 (06_heal_lora write_config line 294 ignored --iters → LR ramped INTO the run → loss-spike). Research (arXiv 2602.04998, Unsloth, RS-DPO): α=rank (16 not 20), warmup=5% of steps, lr 2e-5 (rejection-sampling SFT recipe), dropout 0.1, 1-2 epochs. FIXED write_config (warmup=max(5,iters//20), dropout 0.1). VERIFIED config flow: write_config(args) runs UNCONDITIONALLY → regenerates yaml from CLI args every run (manual edits overwritten; pass ALL args). STABLE recipe confirmed: `06_heal_lora --skip-data --data heal/recover_data --num-layers 8 --rank 16 --scale 16 --learning-rate 2e-5 --iters 150 --batch-size 1` → loss 0.03-0.12 stable through iter 60+.
⚠️ DATA-SCALE TRUTH: 123 examples MEMORIZES (loss→0.02) — far below rejection-sampling scale (RS-DPO=9000). Recipe prevents DAMAGE but a real gain needs 10-50× more data → scale the flywheel corpus before expecting #114 to move the needle. The free-flags + kv-bits + native-tools wins are INDEPENDENT of the heal.

## 📊 #114 recovered-adapter benchmark (HONEST, 2026-06-21): NEUTRAL
recovered (heal/adapters-recover, 123-ex, fixed recipe scale16/warmup7/lr2e-5, stable) = 3/4 = baseline 3/4.
disclosable 1/2 (div_ceil PASS, off-by-one FAIL — needs the new fn-level fallback), subtle 2/2. No regression, no gain.
CONFIRMS the research: 123 examples MEMORIZES (final loss 0.015), doesn't generalize → neutral. The fixed recipe
prevents DAMAGE; the REAL #114 gain needs 2000+ examples (RS-DPO=9000). Recipe is now safe + correct for the scaled re-heal.
PROVEN wins (heal-independent): #121 NATIVE tool_calls at :8080 ✅, #117 INT8-KV active (decode ≈baseline 10 tok/s = memory/long-ctx lever), #120 free-flags live.

## 🔬 #81 + #117 kernel verdict (2026-06-21, research-first → DON'T BUILD)
DEEP RESEARCH on the two "net-new M5 kernel" items concluded BOTH are not worth building:
**#81 Metal-4 fused-MoE kernel — DROP.** (1) MLX gather_qmm ALREADY uses the M5 Neural Accelerator (NAX variants, K%64==0, auto in 0.31.2) — our quantized MoE matmul already taps it. (2) Decode is memory-BANDWIDTH-bound, NOT compute-bound (Apple: "generation is memory-bandwidth-bound… no software optimization changes that limit"). A faster matmul kernel can't speed decode. M5's 153GB/s (+28% vs M4) already gives the ~20-27% decode gain automatically; the NA's 4× is prefill (already captured). Nothing to build. Only decode lever = fewer bytes/token (measured-dead) or fewer STEPS (best-of-N, done).
**#117 TurboQuant 3-bit KV — DEFER (adopt-not-build, only if long-context).** Native 8-bit QuantizedKVCache is ACTIVE (#120) + sufficient for SHORT-context agentic coding (KV isn't our bottleneck, the 99GB weights are). TurboQuant 3-bit = 4.6× compression BUT (a) naive MLX port = 0.5× decode (dequant-on-fetch); only arozanov/turboquant-mlx fused-kernel port = 98% speed, (b) 3-bit K destroys greedy decode → need mixed K8/V4. Worth ADOPTING (their port, not ours) ONLY if/when long-context on big repos becomes the use case.
**The ONE real kernel frontier: sparse-DSA PREFILL attention (O(L²)→O(Lk)) for long prompts — "weeks, hard", only matters at long context.** REAL speed levers now: accuracy (flywheel) + fewer steps (best-of-N).

## 🔬 #115 prompt-lookup spec-decode (2026-06-21): VALIDATED but workload-specific
Built src/spec_decode.py — prompt-lookup speculative decoding (n-gram draft from prompt, model verifies K
in one pass, reuses mlx-lm's verify+cache-rewind). CORRECTNESS: output token-identical to greedy ✅.
SPEED is acceptance-dependent: on PURE-CODE-REUSE output (raw prompt, fix≈input) = 2.5× (15.8 vs 6.3 tok/s,
56% drafted-free). BUT on the flywheel's CHAT-WRAPPED fix-gen (model writes explanation+code → low reuse)
= NET SLOWER (~4 tok/s) — the overhead of verifying 10-token drafts that get rejected exceeds the saving,
AND in-process fixes didn't pass (output-quality differs from the serve path). VERDICT: prompt-lookup helps
FIM/code-COMPLETION (high reuse, no chat wrapper) — bank it for the product's completion path (#35), NOT the
chat flywheel. Reverted to the serve flywheel (the proven workhorse, reached 225). Lesson: spec-decode gain
= f(draft acceptance) = f(output-reuses-input); measure on the REAL workload, not a reuse-heavy benchmark.

## 🔬 Accuracy lever (2026-06-21 research): difficulty-targeted selection + strong verifiers
Speed levers EXHAUSTED this session (Metal/kv-bits/spec-decode-chat/vecstore/callsieve-EP all measured no-gain
or workload-mismatched — speed is near-optimal). Pivot to accuracy. Research:
- arXiv 2404.17140: refiners benefit from more FT data ONLY with STRONG verifiers (oracle), not weak self-verify.
  → our execution verifiers (cargo/pytest) are the RIGHT setup; the flywheel premise holds.
- arXiv 2506.05316: difficulty-targeted online data selection reaches same perf with 13-57% FEWER steps by
  prioritizing INFORMATIVE (hard) samples. → #124: at the 500 re-heal, UPWEIGHT hard fixes (where greedy fails /
  high best-of-N candidate index = the model can't one-shot it) so the small corpus punches above its size.
  Cheap impl at re-heal serve-stop: greedy-rescore each kept fix; greedy-FAIL → hard → duplicate 2-3× in train.
NEW TASK #124 difficulty-weighted re-heal (research-backed data-efficiency; addresses neutral-123 + slow-flywheel).

## 🦀 merle product progress (2026-06-21): agent loop + embedded callsieve + verifier-gated termination
- merle Rust CLI now: `fix` (verified), `explain`, `do` (agentic tool-loop), bare `merle` (interactive REPL like Claude Code), `context` (embedded callsieve retrieval). All MIT, public.
- `do`/REPL agent: model drives native tool-calls (read/list/grep/write/run); PROVEN — fixed calc.py end-to-end via tools.
- VERIFIER-GATED TERMINATION: agent stops as soon as `--test` passes (don't wait for the 3-bit model to call `done` — it often doesn't). Wall-clock + reliability win for agentic coding.
- callsieve EMBEDDED as a Rust lib (merle 2.3M→8.0M, one binary): callsieve::{indexer::build_index, query::build_context, context_read_first_files}. `merle context` works serve-free.
- NEXT: wire callsieve context into the agent's tool-loop (smart localize); vecstore memory (needs embedder choice + recall design).
22:53 v3 RAW (soul-targeted 4-bit, 98G): FOCUS-9 all coherent — py✅ go✅(thin-quirk) ts✅ pg✅ · ~5.5tok/s · gate PASSED → healing
00:53 #113 fix-packet++ (assertion-spotlight in fix prompt): MEASURED — subtle return/comparison flip (clamp return x→hi) resolved on candidate 1, the weakness best-of-N missed. merle committed, not reinstalled. Single-case demo (not full suite). Next rung: #118 Reflexion.
01:20 #118 Reflexion (verifier-feedback retry) BUILT in merle cmd_fix. Measurement INCONCLUSIVE — harder merge_sorted missing-line bug not fixed by v3 even with reflexion (candidate-1 no-change + syntax-error candidate). Model-limited not mechanism-limited; NOT faking a win. Honest data point: v3 fixes simple flips (#113✓) but weak on multi-step. Next: #114 verifier-gated re-heal (the real lever for a weak base) + clean merle file-path-relative-to-repo bug noticed.
02:03 #107 smoke-test: 7/7 LIGHT multimodal lanes WORK (embed/rerank/NER/tabular/RAG/web-search/TTS all produce real output — backing models present). Heavy lanes (imagegen/whisper/video/VLM=GPU) deferred to GPU-idle. MULTIMODAL_SMOKE.md written. Tooling is verified-working not just wired. Flywheel 311 gold (+26), base re-heal at +40.
02:25 #114 HONEST: flywheel generated 39 fixes but only 17 unique-vanilla after dedup, ALL MBPP Python flip-bugs (return→return not) — LOW diversity, does NOT target the Go/JS + multi-step weak spots. heal/heal_v3b BUILT (815 ex, base+17) but a 40min re-heal on +17 marginal Python examples is NOT worth the GPU — won't fix weak spots. CORRECTION: flywheel needs to TARGET Go/JS + harder bugs to make the re-heal matter; current MBPP-Python gen is the wrong gold. Defer re-heal until a diverse batch (Go/JS incl). Not burning GPU on a marginal heal — that's the honest 'chase real gains' call.
02:48 SECURITY soul: found+fixed 2 data-prep bugs — (1) vanilla-filter wrongly applied to security (framework vulns ARE the subject), (2) dedup-on-truncated-system-prompt collapsed 85→9. Re-prepped: 76 train + 9 valid. Heal LAUNCHED on q4a4-v3 → adapters-soul-security-v3 (200 iters). LESSON: souls aren't data-starved, the prep was buggy — apply to all souls (dedup on user-msg, no vanilla-filter for non-code souls). Heal RUNNING.
08:44 SECURITY SOUL — HONEST NEGATIVE (measured A/B): BASE v3 gives ELITE SQLi answer (names parameterized queries), SECURITY SOUL gives GENERIC — the soul DEGRADED security, the thing it should improve. Password-hash = garbage on BOTH (base weakness, demolished model degenerates on some prompts). 2nd soul-degradation data point (v1 soul-adapters garbled too). CONCLUSION: demolished 4-bit base is at CEILING — base re-heal=wrong-gold-marginal, soul-heals=DEGRADE. NOT shipping security soul. NOT blind-healing 8 more souls. Next: ONE gentler-recipe test (rank 8, iters 60, num-layers 3) to confirm fundamental-vs-recipe, else accept base ceiling + value=merle harness+honest research map.
09:28 GENTLE soul DECISIVE: gentle (rank8/iters60) = NEUTRAL — SQLi coherent≈base, password-hash garbage=base (no degrade, no LIFT). vs aggressive (rank16/iters200)=DEGRADE. VERDICT: aggressive heals destabilize the 4-bit base; gentle heals are neutral (no value-add). Souls DON'T improve the demolished base. Password-hash garbage on base+both souls = fundamental 4-bit degeneration. MISSION CONCLUDED honestly: demolished model at ceiling. MISSION_SUMMARY.md written. PIVOT loop off soul-grinding → merle polish + doc-sync + honest benchmark. Real value = merle harness + research-map + working v3 base + multimodal 7/7.
10:10 ✅ FIRST HONEST v3 BENCHMARK: HumanEval pass@1 = 19/20 (95%), n=20 single-shot, real-verifier-scored. BALANCES the picture — the demolished v3 base IS competent at writing vanilla FOCUS-9 functions from spec (its core task). CAVEAT: n=20 = easier end of HumanEval; still fails harder debugging/multi-step + off-distribution (perfumery/password-hash). 'At ceiling' = can't IMPROVE it (heals don't help); current LEVEL on simple code is solid. A harder subset (n=100-164) = the proper fuller number (slow ~2hr, follow-up). MISSION_SUMMARY.md updated.
11:31 ✅ DEFINITIVE #105: HumanEval-164 pass@1 = 114/164 (69%), full set single-shot real-verifier-scored. (easy n=20=95% overstated.) 69% = mid-tier usable for a demolished 4-bit laptop model, ~GPT-4-class on this metric, below frontier coders ~90%; verify-loop lifts it. FINISHING phase ~complete: docs syncing, mission concluded honestly. The fork is the user's: stop (working artifact+merle+research-map) or up-path (methods→clean Qwen-30B). 
