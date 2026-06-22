# Backlog — GLM-5.2-Demolition

> **🎯 GOAL (2026-06-21, standing):** make ours an *amazing* all-local agentic coder — chase **compounding 3×–10×** on **both speed AND accuracy**, knock out the backlog, and keep this a **LIVING document** (change paths as the data says). **Research until possibilities are exhausted.** Order: accuracy before speed · M5-native libs (Metal4/MLX/CoreML/Accelerate) · CallSieve cross-platform feeding all six chips. The levers MULTIPLY — see the SPEED+ACCURACY ROADMAP below.


**SPEED VERDICT (2026-06-21, research-first):** #81 Metal-MoE-kernel DROPPED (gather_qmm already uses M5-NA; decode bandwidth-capped — nothing to build). #117 TurboQuant-3bit-KV DEFERRED (native 8-bit active+sufficient short-context; adopt arozanov fused-port only if long-context). Real speed = fewer-steps(best-of-N done)+accuracy(flywheel). Only kernel frontier left = sparse-DSA prefill attention (hard, long-ctx only).


**#124 (2026-06-21) difficulty-weighted re-heal** — research-backed (arXiv 2506.05316): upweight HARD fixes (greedy-fails) at the re-heal so 500 informative examples ≈ a much bigger uniform heal. Apply at the 500 serve-stop: greedy-rescore → dup hard ones 2-3× in train.jsonl. Speed levers EXHAUSTED (all no-gain); accuracy is the live frontier.


**#125 (2026-06-21) PRODUCT layers — one engine, many faces** — `coder` CLI ✅ built (scripts/coder.py: fix/do/explain over callsieve→model→best-of-N→verify→repair; structurally tested, needs a serve-window end-to-end test). NEXT: native **SwiftUI macOS desktop app** (most 'metal' — Apple-native GUI→MLX-on-Metal model, no Electron/cloud) as a THIN shell over the same engine. THEN VSCode extension (same engine again). Discipline: the CLI is the engine; app/ext are faces — never reimplement the loop. Sequence: prove CLI → app → ext.

**#126 (2026-06-21) FULL instruction-coverage in the product** — the MODEL + ecosystem already handle a vast instruction surface (general chat/reasoning + 20+ specialized lanes: code 7-lang #36-45, design/color/CSS, math/Lean/SymPy, vision #43, image/video-gen #42/44, audio ASR/TTS #92/99, tools #45, tabular #94, omni-router #103). But the `coder` CLI currently exposes only the CODE slice (fix/do/explain). Exposing the FULL surface (design/math/vision/audio/tools subcommands, or a single `coder ask` that routes via #103) = BACKLOGGED. Decision needed: focused code tool vs everything-tool.


**#127 (2026-06-21) GOAL: demolition PUBLIC when ready** — GLM-5.2 is MIT (Z.ai Pure-Open) → our derivative weights+code CAN be redistributed publicly; privacy is TIMING not law (corrects old 'must stay private'). Obligation: include MIT license + credit Z.ai. Readiness gates: (1) honest MODEL_CARD #109, (2) accuracy proven #114 + benches #62-67, (3) glm52-demolition → real git repo (NOT git today) + cleanup, (4) SECURITY scrub (no tokens/keys), (5) polished README + story. Split: merle=private product, callsieve/vecstore=public OSS, model=private-for-now→public-when-ready.


**#128 (2026-06-21) v1→v3 PORT LIST — v3 = 4-bit soul-targeted, RE-PRUNED from mxfp4, so NOTHING from v1 auto-transfers** (checked 10×, pruned to what ACTUALLY needs doing). v3 = `models/GLM-5.2-q4a4-v3` (98GB, 78 layers, 4-bit g64, vocab 154880, FOCUS-9 vanilla). Mission: all-in on GLM-5.2 (no Qwen), **base + swappable souls**.
- **🔄 MUST RE-BUILD on v3** (v1's 24 adapters are bolted to 3-bit layers — won't load on the 4-bit re-prune):
  1. ✅ **Base heal** (FOCUS-9 vanilla code, heal/heal_v3_base 718ex) → `heal/adapters-v3` — DONE (healing now, loss ~0.70).
  2. ⬜ **Soul adapters** re-heal on v3: **design · science · security · math(lean)** — data staged in `heal/souls/` but THIN (design 11/security 11/science 3/math 2) → ENRICH then `06_heal_lora --model q4a4-v3` per soul → the swappable-soul library (#73/#112). v1's adapters-{design,science,security,lean,sound} are the DATA source, not loadable weights.
  3. ⬜ **MTP head** — CONFIRMED ABSENT in v3 (model-extra.safetensors = only lm_head/embed; config num_nextn=1 but no weights). Port the nextn layer from `models/GLM-5.2-mxfp4` (or BF16 original) + 4-bit quant → unlocks self-spec-decode (#69) = the real speed lever.
- **⬜ ENRICH (measured gap):** Go + JS vanilla gold — thin (4 ea) in base; flywheel/gen more, re-heal.
- **VERIFY (likely OK):** DSA patch (glm_moe_dsa) — v3 served+responded so it's applied; confirm on healed serve.
- **✅ NO PORT NEEDED (parity / model-agnostic):** vocab (154880=154880); serving stack (serve_stable/supervisor/watchdog/circuit-breaker), verifiers (5-lang), flywheel, constrained-decode, Lean prover, agent_gateway, merle/callsieve/vecstore, ANE lanes — all work with v3 as-is.
- **❌ DELIBERATELY DROPPED (do NOT port):** gamedev/perfumery/fullstack/factory/grpo/repair/v4/v4-rft adapters (off-mission/superseded); C/C++/Swift/Ruby/Java = separate soul-swap, not core.
- **THEN:** measure healed-v3 FOCUS-9 + clean decode tok/s · push private (rename …-q3a4-MLX → …-q4a4-soul-MLX) · cleanup intermediates (v2src/v3src, keep mxfp4 original).

Kanban by status: **✅ Done · 🔄 In Progress · ⬜ Not Started**. Honest. The live queue is Claude Code's
task list (#1–88); this file is the durable mirror. Detail of done work → OVERNIGHT_LOG.md / BUILD_NOTES.md.
Synced 2026-06-21 (part 9 below). Earlier — part 8 — **EXTERNAL REVIEW absorbed**: verdict = special ARTIFACT, not frontier-PROOF (matches WHAT_MAKES_US_SPECIAL.md). Card TIGHTENED (#109 ✅: HumanEval 70%, adapters 1.9GB not ~100MB, GSM8K/Algebra WITHHELD as inconsistent, serve example → serve_stable.py). New tasks **#110 MoE-Sieve adapters (1.9GB→500MB, arxiv 2603.24044 verified) · #111 paired proof-matrix (Aider/MBPP/LiveCodeBench/BFCL/scored-SWE-bench/FeatureBench) · #112 mounted multi-adapter serving**. Souls PUBLISHED to private HF (**#106 ✅**: philipjohnbasile/GLM-5.2-Demolition-q3a4-MLX — 21 final adapters, checkpoint-filtered to ~2GB each, sound-garbage excluded; also the post-crash backup). MTP gate ran: 0% accept but CONFOUNDED — head needs prune-remap 256→77 (#69). calib 24576; magic doc shipped.
**Part 10 (2026-06-21 PM) — PRODUCT pivot + FREE-things audit + native tools. Docs: RESEARCH_2026.md, FREE_VS_CUSTOM.md, GATEWAY.md.** NORTH-STAR clarified (user): make ours a USABLE agentic coder via CLI/VSCode we run ourselves (not a benchmark). Built **scripts/agent_gateway.py** (:8090) = drop-in backend for ANY harness (OpenAI function-calling + Anthropic /v1/messages → aider/Cline/Continue/Codex/**Claude Code**); proven live (defaults kill the 3-bit collapse, tool_calls returned). **NATIVE tool-calling restored**: demolition had DROPPED the chat_template → reinstalled GLM-5.2's tool-calling template into the served model (CPU-proven renders tools; live on next serve restart). **6 agent scaffold leaks fixed** (done-gate _FAIL on "0 failed", apply_patch self-correct + changed-line/ws-flex matcher, clarify→proceed, read_file peek-loop) — zero model bugs. **#113 best-of-N measured 3/4** (subtle flips 2/2 in 1 cand); off-by-one needs function-level fallback. **#114 PIVOT**: FP teacher infeasible (pruned BF16 ≈500GB) → verifier-gated rejection-sampling FT (SOTA-confirmed); diverse MBPP+HumanEval corpus generating now (recover_datagen_diverse.py, concurrent best-of-N). **🆓 FREE-VS-CUSTOM audit (don't rebuild what ships):** mlx-lm 0.31.3 gives FREE — QuantizedKVCache (#117 = just expose `--kv-bits`), prompt cache (#25/#85), RotatingKVCache (#86), draft/spec decode (#10/#115 = `--draft-model` flag), batching (#48/#71), make_sampler, LoRA trainer (06_heal already wraps `mlx_lm.lora`✓). Our serve runs BARE → free flags to add at restart: `--temp 0.6 --top-p 0.95 --prompt-cache-size --decode-concurrency --kv-bits 8`. GENUINELY OURS (verified, keep): callsieve, best-of-N+verifier, **#45 constrained tool-JSON** (mlx-lm has NO response_format/grammar — XGrammar: constrained 3B > unconstrained 70B = our native-tool reliability lever), glm_moe_dsa, the gateway (no GLM parser / Anthropic endpoint in mlx-lm). **VERIFIED on latest:** mlx 0.31.2/mlx-lm 0.31.3/transformers 5.12.1/datasets 5.0.0 all LATEST; macOS 27 + M5 Max NA active. **VecStore** (we own PhilipJohnBasile/vecstore) → adopt as agent persistent MEMORY, not callsieve's per-repo embed. NEW tasks **#120 serve free-flags+kv-bits · #121 gateway+native tools · #122 the product**.
**Part 8 (3-chip night work, in flight ~21:15):** ⚡ GPU clean **GSM8K-40 + algebra** eval on guarded serve (un-withhold the math number caveated in #109) · 🧵 CPU **MBPP-500 cached** (proof-matrix #111; LiveCodeBench/BFCL loader-skipped) · 🧠 ANE **contamination-check** GSM8K/MATH vs gold (the #111 receipts). All 3 chips genuine, no busy-spin. The Mac kernel-panicked once today (unguarded 05_serve.sh + SWE-bench long-context KV) → ALL serving now via serve_stable.py; zero durable loss (disk had everything).
**Part 9 (2026-06-21) — head-to-head verdict + CallSieve shipped:** the overnight A/B (#111) **DEBUNKED "3-bit can't code"** — it was **5 SCAFFOLD bugs, ZERO model bugs**: greedy temp 0.2→0.6+rep_pen; `read_file` 4000→12000 (the bug sat at line 112, past the cutoff); gen-probe MUST set `enable_thinking=false` or output hides in a `reasoning` field → false "serve hung"; 3-bit collapses on long context → keep context SHORT; `apply_patch` too strict → line-match fallback. Once fixed, **ours self-drove read→grep→apply_patch→`cargo test ok` (145 passed)**. Root fix productized: **CallSieve (#6) FIXED + RELEASED v0.5.0** (github tag, CI+release workflows green, 4 platform binaries) — test-aware focus (never points a bug-fix reader at `mod tests`), **working-tree-diff bug localization** (focuses the *changed* fn → raises the multi-callee-failing-test ceiling), bare `#[test]` detection; 208+145 tests + clippy clean; CHANGELOG/version/tag all on `main`. **4-bit requant HELD (#59/#60):** premise collapsed (bits were never the problem) and flat 4-bit ~120 GB is unservable on 128 GB — the long-context weakness is cured by CallSieve's short pinpointed snippets, not precision. **#111 A/B re-running** with callsieve 0.5.0 on PATH (ours-armed pinpoints via the worktree diff) — the loop closes; awaiting real ours-armed-vs-bare win-rate. Next idle-CPU parallel candidate while the GPU serves: **#110 MoE-Sieve** (1.9 GB→~500 MB adapters).
**Part 6 (earlier):** HumanEval 70% measured; SWE-bench cut to n=5 (5/5 patches, guarded serve held — no crash); speed re-mapped (already optimal path, #81 obsolete, #69 measure-first, #108 parked).

---

## 🔄 TODAY (2026-06-20) — live status
1. ✅ **Health-check** — overnight run clean: 7 souls landed (~2 GB each), no OOM, `LOOP_CLOSED` repair-eval **40/40 (100%, within-distribution)**.
2. 🔄 **Benchmark** — ✅ **HumanEval-164 = 116/164 (70%)** hidden-test scored, single-shot. SWE-bench-30 = too slow (5–7 h agentic @ 11 tok/s, prefill-bound) → **cut to n=5 sample** (running, visible progress, `SWEBENCH5_REPORT.md`).
3. ⬜ **Validate + ship** souls to HF (private) — after benchmark.
4. ⬜ **GPU-test** lanes — audiogen #100 + imagegen #42/#101.
5. 🅿️ **Speed (#108) — INVESTIGATED + parked deliberately (see re-map below).**

### 🚀 Speed re-map (10x web research + code-read, June 2026 — the session's big finding)
- **We're ALREADY on the optimized path.** `mlx_lm/models/glm_moe_dsa.py`: MoE inherits `dsv32.DeepseekV32MoE` (`gather_qmm` fused matmul); decode attention gathers top-k KV (true sparse); **M5 Neural-Accelerators auto-on** (macOS 27 + MLX 0.31.2, no flag). **11 tok/s is genuine, not misconfigured — there is no free 2×.**
- **#81 (custom Metal kernel) = OBSOLETE.** The one real gap: **prefill** attention builds full O(L²) scores + a boolean mask instead of a true sparse gather (O(Lk)). *That* is the upstreamable DSA-attention-kernel contribution — weeks, hard, the genuine frontier.
- **#69 (MTP) = revived but speedup UNCERTAIN → measure-first.** mlx-lm PR #990 (OPEN, native MTP) separates a reusable draft/verify loop from a per-model interface & **explicitly names GLM-5.2**; MTPLX (Apache-2.0) forkable; we already wrote `glm_moe_dsa` (#49). BUT PR #990's MLX MoE testing = **only 1.09–1.11×** (single-layer MTP can't predict expert routing) — NOT the 2.6× (that's NVIDIA full-precision). BF16-vs-quant MTP head is DISPUTED. Plan: time-boxed prototype that MEASURES acceptance + tok/s on our model before committing. Needs the BF16 MTP head from the original (mxfp4 dropped it).
- **#108 = parked, not abandoned.** Upgrade = few-% (already optimized) × real risk (breaks the hand-patched `glm_moe_dsa` + serve). Do it careful + rollback-ready, as its own step — not rushed before 6pm.
- **#23 calib** = REAP mix assembled **20,480/24,576** (evol 4096 + Mixture-of-Thoughts 12288 + SWE-smith 4096; gated xlam needs HF access). Pre-fetched GSM8K/MATH-500/MMLU for the bench sweep.
- **Sound-flywheel bug** = referenced `adapters-soul2` missing the `heal/` prefix → 0 takes generated → sound soul healed on 4 seeds (throwaway). Parked low-pri (1-line fix; model facet, not core).

---

## ✅ DONE

### Foundation (#1–50)
- **Demolition pipeline**: stream-calibrate → REAP prune (256→77 experts) → mixed quant (q3a4, 99 GB) → LoRA heal → serve. One 128 GB Mac.
- **51-tool ReAct agent** + 5 defense layers; verified + constrained decoding; the **verifier mesh** (5 langs + SQL + SymPy + Lean + design render-critic).
- **Formal-math infra**: Lean-4 foundation → expert-iteration → self-correction → the prover agent (`66_prove`).
- **Serving stability** (watchdog/circuit-breaker/mem-ceiling), continuous batching, the **self-healing flywheel**, the `mlx_lm` patch + upstream PR (#49/#50).
- **10 constrained validators** + the **multimodal stack** (vision/image/video/tools).

### Session 2026-06-18
- Tools → vision **Qwen3-VL-4B-8bit**, embeddings **bge-large**, code_intel **5 langs**, +4 tools (**51** total).
- Eval honesty → contamination checks (HumanEval/GSM8K/miniF2F clean, on HF `eval/`); **#61** calib → 1.5M tokens.
- Harnesses built + selftest-green: `dynamic_bits` (#59), `kl_eval` (#60), `swebench` (#62), `86_scoreboard`, `87_lean_study` (#68, study⟂test proven).
- **Speed SETTLED** — speculative measured-dead 4 ways on this memory-bound MoE; real speed = fused kernel (#33) + batching (#35/#48). `SPEED.md`.
- **#31 miniF2F DONE** — 32/226 = 14.2% pass@4, Lean-verified, contamination-checked.
- `adapter_router.py` (mixture-of-specialists) + `88_verifier_distill.py` — built, selftest-green (GPU run pending).
- **#71 throughput batching** wired as the serve's headline speed feature.

### Session 2026-06-19 (this push — "THE local agentic coder")
- **The factory**: soul2 ✓ + **soul-v3 ✓** shipped (HF); `heal_queue.sh` driver autonomous.
- **CPU parallelism**: `verify_many` — verifier mesh fanned across all 18 cores (**6.6×** measured), wired into proof-search.
- **#59 prep**: **NVFP4** wired into `24b_stream_requantize --nvfp4` (half the 3-bit error + M5 2× hardware path) + `04b --bit-choices`.
- **#78 ✅ ANE embeddings** — Apple `NLContextualEmbedding` (no coremltools), `src/ane_embed.py`, backend=ane 768-dim verified.
- **#85 ✅ SSD prompt-cache persistence** — `save()/load()` + keyed warm-start path; round-trip selftest PASS.
- **Research + positioning** (HF): `AGENTIC.md`, `research/agentic_coder_landscape.md`, `research/mlx_speed_deepdive.md`, `research/swappable_adapters_sota.md`; 23 agentic-gold examples staged.
- **ANE/CPU capability sprint** (all GPU-free, verified): **#78** ANE embeddings ✓ · **#79** ANE OCR ✓ (reads tracebacks off screenshots) · **#89** ANE rerank ✓ (YAML ranked top) · **#80+#93** ANE zero-shot router ✓ (5/5 facets) · **#83** concurrent compile∥lint ✓ · **#85** SSD warm-start cache ✓.

### Session 2026-06-19 (part 2 — "use everything": parallel hardware + fast/correct)
- **#59 SETTLED (measured-negative)**: KL-eval ran — v5c (saliency 2-bit) KL=1.11 vs v4 KL=0.59 — **2× worse quality for 1.47× speed**. v4+soul2 stays. nvfp4 + Hadamard both measured-dead GPU-cheaply. +5 research rounds → `research/quant_heal_speed_sota_10rounds.md`.
- **fast+correct plan** (15 rounds): **#1 fast_correct** ✓ (`src/fast_correct.py` — constrained + prompt-lookup DOMINO combine, 100% valid + 2-4× on code) · **#3 early-termination** ✓ (doomed-abort in agent loop) · **#4 speculative-actions** ✓ (`src/spec_action.py` — ANE predicts next tool, 4/5).
- **All 6 M5 blocks tapped**: 🧠 **#90** ANE perception-extras ✓ · **#91** ANE audio+VAD ✓ (440Hz→tuning_fork) · **#92** ANE TTS ✓ (180 voices) · 🎥 **#88** Media-Engine decode ✓ (off-GPU) · ⚙️ **#75** compile-verify ✓ (9 langs +C/C++/Ruby/Swift) · **#82** parallel best-of-N ✓ (3.3×) · **AMX/SME** live (2129 GFLOP/s via Accelerate).

### Session 2026-06-19 (part 3 — "12h across the board" + the loop closes)
- **All chips saturated ~12h, autonomous**: ⚡ `factory_chain.sh` (7 souls, wait-for-GPU→heal→next) · 🧵🧠 `hardneg_flywheel.py` (CPU `verify_many` + ANE embed) · 🎥 `media_flywheel.py` (VideoToolbox H.264 encode). 4 compute blocks lit the whole run; **gamedev soul ✅** + the chain **auto-advanced to legacy with zero intervention**.
- **Flywheel ENRICHED + the compounding loop CLOSED** — `hardneg_flywheel` upgraded arithmetic → **15 real-algorithm templates** (binary-search/Kadane/gcd/RLE…) with computed asserts + realistic bug-injection. `hardneg_to_sft.py` (mine→repair-SFT) + `post_chain.sh` (auto: prep→heal `adapters-repair`→`repair_eval.py`) = **mine → heal → measure, unattended** (writes `LOOP_CLOSED`).
- **Lanes fixed + omni completed**: **#42/#101** `imagegen.py` re-wired to the new mflux API (params MATCH; img2img via `image_path`) · **#100** `audiogen.py` wired (mlx_audio `generate_audio`) — both GPU-test-pending · **#103** `omni.generate()` adds the OUTPUT side (text→image/audio/speech) = true any-to-any.
- **HF + docs**: model card pushed (6-block + factory sections) → the private repo README · `AGENTIC`/`FACTORY`/`RECIPE` updated.

### Session 2026-06-20 (part 4 — sound facet (model-only), audits, discipline)
- **Sound = a real soul facet (b)** — canon (`research/elite_sound.md`) + theory (`music_theory_history_10rounds.md`) + SOTA-vs-Suno research; **`verify("sound")`** (`src/sound_verify.py`: harmony/LUFS/Dilla-feel/earcon, good+bad audited) + sound gold (`build_sound_gold.py`) + `sound_chain.sh` → `adapters-sound`. The verify→gold→heal facet, **not** a music app.
- **Discipline correction** — built then **YEETED** the music-production app (perform/room/liveness/compose/ticket_stub + 3 app-vision docs); kept only the model facet. *"This is a model, not an app."*
- **#26 verifier-mesh audit ✅ clean** — 9/9 languages discriminate good vs compiles-but-wrong, **0 skips** (all toolchains present → no silent false-passes), 0 bugs. The heal rewards are trustworthy.
- **#23 REAP calib ✅ recipe-ready** — `prep_reap_calib.py` encodes Cerebras's ICLR-2026 mix (24,576 @ 16,384) + the **March-2026 saliency fix** (renormalize top-k router logits, ~+0.7pp) for the next prune.
- **Pipeline tidied** — 3-stage autonomous chain (factory → post → sound); flywheels stopped after banking 6,156 hard-negs (diminishing returns) → down to 3 shells.

---

## 🔄 IN PROGRESS
- **#111 head-to-head A/B (re-run, 2026-06-21)** — ours-armed-soul2 (CallSieve 0.5.0 diff-pinpoint snippet) vs ours-bare-soul2 over real callsieve bugs in isolated git worktrees, scored by `cargo test` exit code. Crash-safe (serve_stable :8080, MLX_MEM_GB guard, gen-probe `enable_thinking=false`). `scripts/headtohead.py --ours-soul soul2`; log `/tmp/OURS_RUN2.log`, results `HEADTOHEAD.jsonl`. Awaiting first real ours-armed-vs-bare pass-rate → then decide full overnight fight (+ cloud agents claude/codex/agy) vs benchmarks. **#6 CallSieve: DONE — v0.5.0 released** (the localization fix that unblocks this A/B). **Propagated project-wide:** every runtime call resolves via `$CALLSIEVE_BIN || which callsieve || ~/.local/bin/callsieve` → all = 0.5.0 (includes the agent's OWN `search_code` tool in `57_tool_agent.py:30`, the `28_callsieve_protocol` generator, and the harness); one binary on the machine, no env-pins, no stale `.callsieve` indexes. Only historical footprint: `heal/mine/callsieve_protocol.jsonl` (Jun 16) was generated pre-0.5.0 — already baked into the souls, optional regen with 0.5.0 on the next re-heal.
- **Factory chain (GPU, ~15h queued)** — gamedev ✅ · legacy ✅ → **security healing** → fullstack · science · factory · perfumery (each `adapters-<spec>` on v4; auto-advances). Measured **~2.3h/soul @ ~0.12 it/s** — heal at the M5 ceiling (no safe speed-up: seq pinned 2048 = DSA crash, batch>1 OOMs, #81 kernel is weeks).
- **The autonomous pipeline (3 shells)** — `factory_chain` (souls) → `post_chain` (repair soul: heal on the **6,156 banked hard-negs** + eval → `LOOP_CLOSED`) → `sound_chain` (sound soul, facet b). The 2 downstream waiters sleep at ~0% until their marker fires. *(flywheels stopped — enough negs banked.)*
- **#42/#101 gen-media** ✅ RE-WIRED · **#100 audio-gen** ✅ WIRED — both GPU-test-pending behind the chain.
- **#17 Design-soul heal** — folded into the soul line.

---

## 🔬 SPEED + ACCURACY ROADMAP (2026-06-21, research-backed) — *accuracy before speed; GPU-gated, do in order*
Decided: stay on GLM-5.2; make it RELIABLE then FAST; CallSieve stays cross-platform with **optional** Apple-Silicon accel (feature-flag, never Mac-only — retrieval quality is platform-agnostic; only the accel layer is Apple-specific). June-2026 SOTA mapped to our system (744B MoE, 3-bit, M5 Max, ~11 tok/s, prefill-bound). Proven today: the **fix-packet** (snippet + failing-test-names + "apply_patch NOW" directive) makes ours decisive — step-1 edit vs an 8-step gather-loop — but only on *disclosable* bugs (div_ceil); subtle ones (`>/<`) still miss → best-of-N is the lever.

**① Accuracy (foundation, GPU-gated — first when the A/B frees):**
- **#113 best-of-N + verifier-gated fix [✅ VALIDATED]** — at the fix step, propose N candidate patches; `cargo test` / verifier mesh picks the right one. Cracks subtle bugs (the model proposes `>` AND `<`, the test disambiguates). WIRING job — pieces exist: `src/batched_gen.py batched_best_of_n_parallel` (#82) + `src/verifiers.py verify_domain/verify_many` (#26) + the agent's `verify` tool. (CWM: test-time compute = +12pt SWE-bench.)
- **#114 QAD heal (quantization-aware distillation)** — distill the full-precision GLM teacher into our 3-bit student via KL loss → recover ~99% of BF16 accuracy at the SAME 99 GB (no size change → sidesteps the unservable-4-bit wall). The new research lever; lifts EVERY task. Overnight GPU run. Reframes the held #59/#60 4-bit path.

**② Speed (once reliable):**
- **M5 Neural-Accelerator prefill** (= **#108** + **#81** Metal-4 TensorOps) — Apple measured ~4× TTFT / prefill (decode is bandwidth-bound, ~1.2×). We're PREFILL-bound (re-send codebase context each step) → biggest speed win, mostly an MLX/macOS-26.2 software upgrade.
- **#115 CallSieve-fed speculative decode** — callsieve supplies exact code spans as draft tokens; the serve verifies in bulk (RASD / FastCoder / SpecAgent, the published 2026 retrieval-spec pattern). The real fix for 11 tok/s decode. callsieve FEEDS the GPU — cross-platform; accel is serve-side.

**③ Chips / retrieval polish (parallel, optional — the "all the chips" directive):**
- **#116 CallSieve `embed`→ANE** — turn on callsieve's gated `embed` Cargo feature + route to ANE/CoreML (#78) for semantic retrieval on the Neural Engine. Optional `--features` build, NOT Mac-only. Lower priority (lexical+diff already pinpoint).

**④ Prove (after ①–②):** #111 paired proof-matrix vs local rivals + #105 HumanEval-164/SWE-bench — honest numbers (note: 2026 SWE-bench is saturated/gamed; chase real steps-to-fix wall-clock, not the leaderboard).

### 🔭 More research-backed levers (2026-06-21 deep dive) — they COMPOUND toward 3×–10×
**SPEED stack (multiplicative across the agentic loop):**
- **M5 Neural Accelerators / Metal-4 TensorOps** (#108/#81) — ~4× PREFILL (we're prefill-bound). Software upgrade (macOS 26.2 + MLX).
- **#117 TurboQuant/PolarQuant KV-cache** — 3-bit KV, up to **8× attention** / 3.5–6× memory, near-zero loss, **MLX-native** (turboquant-mlx, SwiftLM fused Metal). Frees RAM + long context too.
- **#115 CallSieve-fed spec decode** + **#69/EAGLE-3.1** — **3–4× DECODE**. EAGLE-3.1 fixes attention-drift; train a fresh head for our MoE (from scratch, SpecForge; acceptance length ~2.8–3.5). CAVEAT (research): MoE + large draft trees activate many experts → memory pressure can erode spec gains — measure.
- **#119 contextual sparsity** (DejaVu/SparseInfer/Polar Sparsity) — 4.5–11× in hybrid settings; research-y for MoE.
- **fix-packet (DONE)** — fewer STEPS (each saved step ≈ 110s). The biggest wall-clock win already banked.
→ 4× prefill × ~3× decode × KV/step savings = the 10× target is realistic *across the loop*, not on raw tok/s alone.

**ACCURACY stack:**
- **#113 best-of-N + verifier** — +12pt (CWM test-time compute). Cracks subtle operator-flips the fix-packet misses.
- **#118 Reflexion + prompt-opt** — +11pt HumanEval (failure-note retry) and ~2× from MIPROv2-style auto-tuning the fix-packet hint. Cheap (scaffold, no training).
- **#114 QAD heal** — ~99% BF16 recovery at 99 GB (base-model floor lift).
- **fix-packet++** — bundle the failing test's ASSERTION (expected value) so the model infers flip-direction — cheaper than best-of-N for subtle bugs; test both.
- **constrained decoding** (#32/#45) — first-try-correct.

**LIVING-DOC RULE:** re-rank these by *measured* gain as each lands; drop anything that doesn't pay; keep researching new 2026 levers. Update this block every session.

---

## ⬜ NOT STARTED — by hardware tier (trigger phrase in quotes)

### ⚡ GPU (decode + heal — behind the factory)
- **#81** Metal-4 **TensorOps** fused-MoE kernel — ~30–60% decode lever. **M5-only, can't cloud** (no M5 silicon in any cloud; cloud NVIDIA can't run Metal). `research/mlx_speed_deepdive.md`.
- GPU follow-ups: **adapter_router** multi-adapter serve · **verifier_distill** run · live-docs RAG **embed-index** · **GPU-test `imagegen`/`audiogen`** (wired, weights+GPU pending).
- **#69** Fresh EAGLE-3 speculative head — the only single-stream path; weeks-local, not recommended.

### 🧠 ANE — *fully built* (#78 embed · #79 OCR · #89 rerank · #80/#93 router · #90 perception · #91 audio · #92 TTS · #96 CV · #97 NER)
- **#87** Speech-to-text — superseded by **#99** (mlx_whisper). Native `SFSpeechRecognizer` only if a no-download on-device path is wanted.

### 💾 SSD (14.5 GB/s)
- **#86** SSD-backed KV offload → long context (attacks our weakest axis vs 1M-ctx rivals; #85 plumbing done).

### 📊 Benchmarks — *"run the benchmarks"* (all GPU-gated, behind the factory)
- **#62** SWE-bench (✅ harness) · **#63** HumanEval-164+MBPP · **#64** Aider Polyglot · **#65** GSM8K+MATH · **#66** LiveCodeBench · **#67** GPQA+MMLU · **#68** study→test (✅ built) · **#60** KL-eval (✅ harness). → `86_scoreboard`, contamination-checked.

### 🌐 Ecosystem / formats / breadth
- **#51** GGUF + llama.cpp DSA (toolchain ✅) — also the path to a **hosted demo** (→ a bring-your-own-weights endpoint; the HF provider catalog won't serve an MLX/custom model) · **imatrix** · **AWQ** · **quant-ladder** 4/5/6/8-bit.
- **#73** model-factory library (forging now) · **#76** legacy + **#77** security (in the chain) · **#23** Cerebras REAP calib ✅ **recipe-ready** (`prep_reap_calib.py` + the renorm fix, applies next prune) · **#53** demolition-family (deferred) · **#95** GPU gen-media video/3D (low-pri).

---

## 🗺️ Capability map — every HF task type → M5 Max engine → status
*Full-hardware doctrine: **ANE perceives** · **GPU generates + decodes** · **18 CPU cores verify** · **Media Engine** decodes+encodes video (#88/#88b) · **AMX/SME** CPU matrix (numpy/Accelerate) · **SSD** remembers. Legend: ✅ built · ⬜ #N queued. **Refreshed 2026-06-19 (part 3)** — #96/#97/#98/#99/#102/#103 now ✅; #100/#101 wired (GPU-test-pending).*

**Multimodal** — Image-Text-to-Text / VQA / Doc-QA ✅ ANE-OCR #79 + GPU-VLM #43 · Visual Document Retrieval ✅ ANE #89 · Video-Text-to-Text ✅ Media-decode #88 + GPU #43 · Audio-Text-to-Text ✅ #99 · Image-to-Image ✅ #101 (mflux) · Any-to-Any ✅ #103 (omni in+out)

**Computer Vision** — Image-to-Text/OCR ✅ ANE #79 · Image Classification ✅ ANE #79 · Image-Feature-Extraction ✅ ANE #78 · Saliency/Barcode/Rectangle ✅ ANE #90 · Zero-Shot Image Classification ✅ ANE #80 · Segmentation/Mask/Keypoint/Pose/Object-Detection/Depth/Zero-Shot-OD/Contours ✅ **#96** (ANE-Vision) · Text-to-Image ✅ Flux-GPU #42 (mflux re-wired) · Text-to-Video ✅ GPU #44 · Video Classification ✅ **#98** · Image-to-Image ✅ **#101** (mflux `image_path`); Video/3D/Uncond-Gen ⬜ (GPU)

**NLP** — Text-Gen/QA/Translation/Summarization ✅ GPU (model) · Feature-Extraction/Sentence-Similarity ✅ ANE #78 · Text Ranking ✅ ANE #89 · Text/Zero-Shot Classification ✅ ANE #93 · Token-Classification/NER ✅ **#97** (NLTagger) · Table QA ✅ #94 · Fill-Mask ⬜ #97 (low)

**Audio** — Automatic Speech Recognition ✅ **#99** (mlx_whisper-GPU; supersedes #87) · Audio Classification / Voice Activity Detection ✅ ANE #91 · Text-to-Speech ✅ ANE #92 · Text-to-Audio ✅ **#100** (`audiogen.py`, GPU-test-pending) · Audio-to-Audio ⬜ (sts)

**Tabular** — Table-QA ✅ #94 · Tabular Classification / Regression / Time-Series Forecasting ✅ **#102** (CPU sklearn/statsmodels)

**RL / Other** — Reinforcement Learning ✅ GRPO #18 · Robotics / Graph ML ⚪ N/A for the agentic-coder tool

---

## 🔴 Dead / low-ROI (MEASURED — won't run)
- **Single-stream speed = MAXED** (2026-06-18): MTP-port 0%, external-draft/prompt-lookup 0.32×, dsa-block flat, active-experts quality-dead. ~11–14 tok/s floor; real speed = #33 + #35/#48. NVFP4 (#59) + TensorOps (#81) are the *new* M5 levers (≠ speculative). See `SPEED.md`.
- **#20** rotation-quant (≤3-bit lossy) · **#52** mlx-swift port (community-likely; watch, don't duplicate).

## ⏸️ Held (timed, not blocked)
- Card **model-index** (until full HumanEval-164 + SWE-bench land) · **HF Collection** · usage notebook · demo **Space**. *(RECIPE.md ✅ done)*
- **4-bit / mixed re-quant (#59 v6 path, #60 KL eval) — HELD.** The premise ("3-bit can't code") was DEBUNKED on 2026-06-21 as 5 scaffold bugs, zero model bugs (see Part 9). Flat 4-bit ≈120 GB is unservable on 128 GB (v6 @ 111 GB already too big; v4 @ 99 GB is the sweet spot), and the only real 3-bit weakness — long-context collapse — is cured by CallSieve's short pinpointed snippets, not precision. Reopen ONLY if the #111 A/B shows a quality failure short-context can't fix, and even then via a *tuned* mixed plan (≤~105 GB), never flat 4-bit.

## ⏸️ Deferred on purpose
- **#53** Demolition family (64 GB sibling) — depth before breadth; revisit after #59.

## 💡 Ideas (not built)
- 8-facet soul flywheel for **all** facets · a **second demolition lineage** (prove the recipe generalizes).

### 📊 #113 MEASURED (2026-06-21): bestofn_fix over verified bugs = 3/4 (disclosable 1/2, subtle 2/2 in 1 cand each).
The 1 miss = off-by-one `-1→+1` (function-level case per arXiv 2604.00167 — line-level best-of-N can't see the surrounding logic). FIX = add function-level fallback to bestofn_fix (regenerate whole fn if line-level fails N). Subtle operator-flips (the hard class) PASS 2/2. #113 validated for the operator-flip class; function-level fallback pending for off-by-one.
