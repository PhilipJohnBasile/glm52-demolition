# Build Notes — Demolishing GLM-5.2 for a 128 GB Mac (agentic coding + design, beat Fable in-niche)

Running lab notebook. **What works, what doesn't, why**, so we improve the process — not just the model.

## Goal
Best *agentic-coding + design* model **for this stack** (TS/JS/Python/Rust/Go, hand-written
vanilla JS, Postgres, the user's Rust app **callsieve**) on a MacBook Pro M5 Max 128 GB,
that **beats Anthropic Fable 5 in this niche** — via specialization + **best-of-N real
verification** (the proven way a small specialist tops a frontier model) + **CallSieve
zero-token retrieval** (the lever that makes a small local model punch above its weight).

## Pipeline (the one that actually runs on 128 GB)
`stream-calibrate (true REAP) → prune experts → stream re-quantize (mixed) → fix+balance heal data → heal (LoRA SFT) → logit-KD → eval (vs-Fable, code+design) → serve (callsieve MCP + think-proxy + best-of-N)`

The non-negotiable design constraint: **the 381 GB model never fits in RAM**, so *every*
heavy step streams the model **one layer at a time** (`src/weight_store.py`, ~5 GB working set).

---
## WHAT WORKS
- **Streaming layer-by-layer (`weight_store.py`)** — the foundation. Calibrate/prune/requant
  on a >RAM model by bounding the working set to ~one layer. Without this, nothing runs.
- **True-REAP saliency** = `router_weight × activation_norm` (not frequency). Correct
  expert-importance signal; with a **padding mask** + `nan_to_num` it's clean.
- **Mixed-precision quant via per-module config overrides** — experts low-bit (bulk),
  attention/embed/lm_head higher-bit. mlx reads `config["quantization"][module_path]`.
- **best-of-N + REAL verification** (`26_bestofn.py`) — code: run the tests; design:
  render+measure (WCAG/type-scale/OKLCH/framework-tells). Stronger than a learned reward
  model; this is the frontier-beater. Validated: finds a passing candidate among N.
- **Design render→critique loop** (`25_design_critique.py`, Playwright) — measurable design.
- **vs-Fable head-to-head eval** (`07_eval.py --vs-fable`) — turns "did we beat it?" into a number.
- **CallSieve as the context layer** — zero-token deterministic retrieval; reads the right
  5 files instead of grepping 50. Replaces the homegrown embedding RAG.
- **Heal that actually trains: full-sequence LoRA SFT** — `06 --no-mask-prompt --num-layers 6
  --max-seq-length 768` with `GLM_STREAM_EVAL=0` on the 99 GB q3a4 model → finite loss
  (2.45→1.75), peak 110.9 GB. (`--mask-prompt` is the NaN trap; see failure #5.)
- **LM Studio engine patch** (`dist/install_glm_dsa_patch.py`) — the closed app loads the
  model via the open `mlx_lm` it vendors, once we drop in our `glm_moe_dsa.py`.

## WHAT DOESN'T (failures + root cause + fix) — the gold
1. **Naive mmap forward OOMs (~120-150 GB)** even though "loading" seemed fine.
   *Cause:* lazy load deferred the blowup to first forward. *Fix:* stream + per-layer `mx.eval`.
   *Lesson:* "it loaded" ≠ "it runs."
2. **mlx-lm: "Missing 285 parameters" (indexer.*)** loading GLM-5.2.
   *Cause:* `glm_moe_dsa` has 21 *full* DSA layers that own an indexer + 57 *shared* that
   reuse the prior full layer's topk (groups of 4). *Fix:* patched `glm_moe_dsa.py`
   (`GlmDsaAttention(is_full)` drops indexer on shared, reuses `shared_topk`).
3. **Saliency NaN** from padding tokens polluting accumulation. *Fix:* padding mask + true-REAP.
4. **`04_quantize` can't shrink an already-mxfp4 model** (predicate skips quantized modules).
   *Fix:* `24b_stream_requantize.py` — streaming **dequant→requant**.
5. **Heal "Val loss nan" — MIS-DIAGNOSED FOUR TIMES (the saga, the biggest time-sink).**
   (a) Blamed uniform-3-bit quant → over-corrected to 6-bit attention → bloated 96→103 GB →
   **self-inflicted the OOM in #6.** (b) Blamed prompt>max_seq truncation → built `27b` to
   filter long-prompt rows → it dropped **0 rows** and it STILL NaN'd. **Actual confirmed
   root cause:** `--mask-prompt` divides the loss by the completion-token count; for some
   rows **mlx_lm's own** prompt/completion boundary yields **zero** completion tokens →
   `mask.sum()==0` → `0/0 = NaN` at iter-1 val. Our data filter can't fix it — the boundary
   is computed *inside* mlx_lm. **Fix that worked:** `--no-mask-prompt` (full-sequence loss)
   → `Iter 1: Val loss 2.448` finite, loss falls 2.45→1.75, heal trains. *Forward was never
   the issue:* all 25 val rows forward finite throughout. **LESSONS: (1) reproduce on the
   REAL failing path (mlx_lm's masked loss), don't theorize from a toy forward; (2) don't
   over-correct — the 6-bit "fix" cost a full model rebuild AND caused the OOM; (3) full-
   sequence loss is the robust default for healing (no mask = no 0/0).**
6. **Training OOM at 99-103 GB on 128 GB.** Val (forward-only) fits; first *backward* step
   aborts (`[METAL] Insufficient Memory`). *Reality:* experts are the bulk, so changing
   attention 6→4 bit only saved 4 GB (103→99). **Fix (confirmed): cut training footprint —
   `--num-layers 6 --max-seq-length 768`, grad-checkpoint, batch 1 → peak 110.9 GB, trains
   fine** — NOT quality (keep 77 experts). *Lesson:* on 128 GB, model size and trainable-
   layer count are both hard memory levers; budget ~15-25 GB over weights for a backward step.
7. **Router-KD fails:** `GatherQMM::vjp cannot compute gradient wrt indices`.
   *Cause:* expert *selection* is non-differentiable in mlx. *Resolution:* REAP router-KD is
   a **closed-form renormalization**, and GLM-5.2 has `norm_topk_prob=True` (already renorms
   the kept top-k) → router-KD is **redundant**, honestly skipped (not a loss).
8. **`GLM_STREAM_EVAL=0` for all training/fitting** — the per-layer `mx.eval` (needed for
   >RAM inference) breaks mlx function-transforms during training.
9. **mlx server has no `--kv-bits`** in 0.31.3 (KV-cache quant exists only in `generate`/`cache_prompt`).
10. **HF dataset gotchas:** xlam gated; `open-r1/Mixture-of-Thoughts` needs `config="code"`;
    `SWE-smith-trajectories` split is `tool`/`xml`/`ticks`, not `train`.
11. **CallSieve: ingested its *source* but not its *function*.** Built the user's Rust into
    training/RAG, but missed that callsieve IS the zero-token retrieval layer. *Fix:* wire
    `callsieve mcp` at serve time (retire homegrown RAG) + train the callsieve-first protocol.
12. **LM Studio "can't load it" — SOLVED without the closed company.** The LM Studio *app*
    is closed, but the engine it loads MLX models with is **open-source `mlx_lm`, vendored
    on disk** at `~/.lmstudio/extensions/backends/vendor/_amphibian/*/.../mlx_lm/models/`.
    Stock ships a **53-line stub** for `glm_moe_dsa` (→ "Missing 285 parameters"); we
    overwrite it with our **238-line** impl via `dist/install_glm_dsa_patch.py` (backs up
    `.orig`, idempotent, `--revert`). Patched all 4 local backends → LM Studio loads GLM-5.2
    after a restart. *Lesson:* "closed app" ≠ "closed engine" — patch the open layer it
    bundles. (Optional next: PR the fix to mlx-lm + lmstudio-ai/mlx-engine upstream.)

## Memory budget reality (128 GB)
| artifact | size | note |
|---|---|---|
| GLM-5.2-mxfp4 (orig, 256 experts) | 381 GB | never RAM-resident; stream only |
| pruned-v2 (77 experts, mxfp4) | 117 GB | stable but too big to train |
| q3-v2 (experts 3b / attn 6b) | 103 GB | over-corrected; OOM'd training |
| **q3a4-v2 (experts 3b / rest 4b)** | **99 GB** | **current; forward-finite on real data** |
- Training needs ~15-25 GB over weights for a backward step → keep weights ≤ ~100 GB and
  cut `--num-layers`/`--max-seq-length` to fit. Forward-only (serve/eval) fits at 99-103 GB.

## Decisions: add vs skip (toward beating Fable in-niche)
- **ADD:** logit-KD (strongest recovery), callsieve-in (token saver), thicker agentic data
  (edit→test→fix loops), design-vs-Fable eval, speculative draft *if a compatible draft exists*.
- **SKIP:** DWQ (logit-KD subsumes it), sensitivity-quant (already mixed), **ParetoQ 2-bit**
  (moves us *away* from Fable — we don't need the space), iterative prune+heal (**defer until
  eval proves the one-shot 77-expert cut is too lossy** — don't burn days of compute preemptively).

## Open questions / next improvements
- ✅ ANSWERED: `--num-layers 6 --max-seq-length 768` heal fits at 99 GB (peak 110.9 GB).
- Does the SFT-healed model beat Fable on `07_eval --vs-fable` (code) + `29` (design)? (run after heal)
- Logit-KD (`20`, teacher=pruned-v2) on top of SFT — how much extra recovery? (task #8)
- Is there a small GLM with GLM-5.2's **exact tokenizer** for speculative decoding? (1.5-2.5×, task #10)
- Active-expert reduction at inference (`22_speed_tune.py`, 8→6) — measure quality vs speed.
- Vocab trim (`30`, build pending) — ~31% smaller head; verify no tokenization drift (task #12).
- After baseline eval: is iterative prune+heal warranted, or do logit-KD + best-of-N close the gap?

## Current status (live)
- Heal v5 RUNNING on `models/GLM-5.2-q3a4-v2` (99 GB, experts-3bit/rest-4bit), full-sequence
  loss, num-layers 6, ~70 min for 1500 iters. Loss healthy and falling.
- Canonical model = **q3a4-v2**. `q3-v2` (103 GB, 6-bit attn) is the over-corrected dead end; `pruned-v2` (117 GB) is the pre-quant teacher for logit-KD.
- Data = `heal/data` (40,473 train) incl callsieve protocol ×3 + callsieve conventions + design + Postgres + stack + reasoning + anti-forgetting.
- LM Studio: fix applied to all 4 local backends (`dist/`).

---
# SESSION 2 (2026-06-17) — the agentic engine, the v4 rebuild, honest gaps

## Built BEYOND demolition (all selftested, GPU-free to run)
- **Verifier mesh** (`src/verifiers.py`) — every domain meets its real tool: compile+run (5 langs)
  + LINT (ruff/clippy/gofmt/prettier = idiomatic, not just compiling) + SQL (sqlite) + math (sympy),
  behind one `verify_domain(domain, output)`. Wired into the 19-tool agent. clippy = the Rust niche.
- **Agentic engine** — `50` deep loop (write→test→repair→refactor, budget + best-of-N), `51`
  multi-agent (coder + ADVERSARIAL tester), `52` flywheel, `53` arena, `54` beam search, `56`
  file-editing harness, `57` ReAct tool-agent (19 tools), `60` PAL+self-consistency.
- **New senses** — `src/vision.py` (VLM SEES renders/screenshots), `src/web_browse.py` (web
  search + Playwright browser), `src/repl.py` (stateful Python), `src/sci_tools.py`, `imagegen.py`.

## WHAT DOESN'T (the gold) — new failures + root cause
- **GRPO regressed 8/12→7/12.** Crash: quantized MoE expert-gather non-diff (`GatherQMM::vjp`).
  Fixed via `mx.stop_gradient` on dsv32 `group_expert_select` inds + grad_checkpoint → it TRAINS
  but won't CONVERGE on this pruned MoE (recent iters 0/6). Reverted to SFT.
- **MATH COLLAPSED 0/5 GSM8K — biggest finding.** v3 REAP calibration was CODING-ONLY → the math
  super-experts never activated → scored ~0 → pruned → collapse (known: arxiv 2507.23279). No tool
  restores a pruned-away expert. → the v4 rebuild.

## v4 rebuild (running): balanced CODE-FIRST calibration (keeps code AND math super-experts) →
re-prune → re-quant → heal/distill on R1 long-CoT traces (the R1-Distill recipe) → eval. Agentic
code is the spine. `61`(calib)→`23`→`24`→`24b`→`06`(heal/data-v4)→`59`.

## HONEST GAPS: "beat Fable 5" never measured (no key/Fable down); speed not benchmarked;
Router/Logit-KD, MTP, HF-publish built-not-run. PROOF = `45_bench_speed` + `53` arena on v4.

## Dev tools added (2026-06-17) — deep-dive verdict: build the worth-it ones
`src/dev_tools.py` (all selftested), wired into the agent (now 23 tools):
- **git** (status/diff/log/branch/commit + **PR via gh**) — the agent SHIPS changes.
- **code_intel** (LSP definition/references/hover via rust-analyzer + pyright; grep fallback) — the #1 coding gap.
- **profile** (cProfile → hot paths) — performance, not just correctness.
- **pg** (real Postgres via psycopg + DATABASE_URL; sqlite fallback) — the niche DB.
SKIPPED (missing binaries / lower value): debugger (awkward for a non-interactive agent), diagram-gen
(mmdc), PDF (pdftotext), SAST (semgrep). Easy to add if the binaries are installed.

## Frontier-parity tools (2026-06-17) — closing the gap vs Claude Code / Codex
Agent now 30 tools. Added: **task** (sub-agent delegation, recursive agent_loop), **apply_patch**
(structured edit vs whole-file rewrite), **todo** (plan tracking), **github** (gh connector: issues/
PRs/api) + **mcp** (generic MCP client — any connector via .mcp.json), **desktop** (pyautogui full-
desktop computer-use; needs macOS Accessibility perm), **read_doc** (PDF/docx via pypdf/python-docx).
This brings the coding-path toolbox to feature-parity with frontier agent harnesses (and beyond, via
the verifier mesh + Lean + callsieve + code_intel they lack).

## Trust layer + voice/video (2026-06-17) — what the community begs for; frontier lacks OOB
Research (Reddit/HN/GitHub): the #1 unmet need is SAFETY/TRUST, not capability (an agent deleted a
prod DB + backups in 9s; 29M secrets leaked in 2025; prompt-injection via PR titles). Built
`src/trust.py` (selftested) + wired into the agent (now 37 tools):
- **checkpoint/rollback** (snapshot before acting, revert on failure), **secret-scan** (block writing
  API keys), **prompt-injection guard** (OBSERVATIONs wrapped as untrusted data), **audit trail**
  (logs/agent_audit.jsonl), **risk gate** (block rm -rf/force-push/DROP/prod unless ALLOW_RISKY),
  **prod-readiness review** (error handling/rate-limit/N+1). A LOCAL agent with these is trustworthy
  in a way cloud can't be (your machine, your git, auditable).
Voice/video (local, no cloud): `src/audio.py` transcribe (Whisper/MLX) + speak (`say`/mlx_audio);
`src/video.py` watch (opencv keyframes → the VLM). Agent tools: transcribe, speak, watch_video.

## Reliability layer + visual-gen + voice/video batch (2026-06-17) — agent now 42 tools
Deeper research: the next unmet need below trust is RELIABILITY-OVER-TIME (context rot 73%@t5→33%@t16;
silent false-success; flaky tests; re-onboarding every trajectory). Built `src/reliability.py`
(selftested) + wired into the loop: **constraint-pinning** (hard rules stay in context every turn) +
**verify_success** (false-success guard) on each observation; tools **onboard** (persistent codebase
map) + **flaky_check** (re-run N to separate flaky from real). VISUAL GEN reframed for the niche:
`render_viz.py` (matplotlib/manim/mermaid/graphviz/TikZ = EXACT, verifiable — the right tool for
math/arch, not diffusion); `imagegen.py` quality-first (Flux.1 dev @8-bit + render→SEE→critique→regen
loop; FLUX.2 klein/dev via mlx-flux2 when installed — pro is cloud, skipped). VOICE/VIDEO: audio.py
(Whisper ASR + say/neural TTS), video.py watch + **transcribe_video** (bundled ffmpeg→Whisper),
video_gen.py (LTX best-effort + manim math-video). All selftested; full gen tested live (GPU).

## Self-improvement + interaction layer (2026-06-17) — agent now 46 tools
Deepest research pass: below trust + reliability sits SELF-IMPROVEMENT + INTERACTION (Voyager skill
libraries; "ask before assuming" = the most-praised 2026 prompt; large-output context overflow). Built:
- **Skill library** (`src/skills.py` + `skill` tool) — distill VERIFIED solutions into named, reusable
  skills; find/get/save/compose instead of re-reasoning from scratch (Voyager/AutoSkill). Persistent
  in skills/*.json → compounds on the user's codebase (a cloud agent can't).
- **Clarify-before-assuming** (`reliability.needs_clarification`/`clarifying_questions` + `clarify` tool
  + loop nudge) — underspecified task → ask, don't assume (HF 2603.26233).
- **Pointer store** (`src/ptr_store.py` + `peek`/`grep_ptr` + loop `maybe_store`) — outputs >3000 chars
  live OUTSIDE context as ptr: handles the model pages/greps (arxiv 2511.22729) — no overflow.

## Integrity layer (2026-06-17) — the verifier is the incorruptible source of truth
Research found the worst 2026 failures are DISHONESTY: Gemini 3.5 fabricated compliance docs + claimed
unmade fixes; Replit's agent faked test results + wiped a prod DB + lied. Built `src/integrity.py`
(selftested) + wired into the agent (no new tools — guards on existing ones):
- **test-tamper guard** (write_file) — block weakening/deleting tests to fake a pass when the task is
  "make tests pass" (reward-hacking); warn otherwise.
- **fabrication-proof done** (agent_loop) — if the agent changed code, `done` is REJECTED unless a real
  verifier PASS is in recent observations. The agent's word is never trusted.
- **scope enforcement** (write_file) — flag edits to sensitive files (.env/CI/locks) or >12 files (creep).
- **slopsquat guard** (run) — `pip/npm/cargo install X` is BLOCKED unless X exists on the real registry
  (hallucinated package names are the supply-chain attack vector). This is our thesis crystallized.

## Humanizer (2026-06-17) — prose verification + voice matching, agent now 47 tools
Content the model writes (comments, commits, PRs, docs, design copy) was reading like AI-slop. Built
`src/humanize.py` (selftested) + `humanize` tool: scores the 2026 slop tells (delve/leverage/seamless/
"in today's world"/em-dash overuse/tricolons/low-burstiness/hedging/sycophancy), LEARNS the user's
voice from their git log (cloud can't), and emits a per-DOMAIN rewrite brief (code/commit/pr/docs/
design/prose). Same loop as code: write → humanize_score → rewrite until >=85 + on-voice. Intent is
craft/voice, not defeating AI detectors. slop scored 18-51/100, plain human prose 100.

## Own-your-repo demo + HF refresh (2026-06-17)
`scripts/64_own_your_repo.py` (harvest/train/demo): harvests YOUR repo's functions into {"messages"}
style pairs, LoRA-fine-tunes so the model writes in YOUR conventions, then a 2-part demo (writes in-style
+ verifies; then tries to make it cheat → integrity layer blocks test-tamper + rejects unproven `done`).
Tested GPU-free: 2,599 style pairs harvested from callsieve. HF: dist/MODEL_CARD.md rewritten current
(51-tool agent, 5 defense layers, v4 recovery, honest license note) + reconciled to root MODEL_CARD.md.

## GPU-ceiling crash fix (2026-06-17) — the root cause of ALL the "random" crashes
Every Metal command-buffer timeout / mid-generation crash traced to ONE thing: the model needs
**~101.6 GB**, macOS caps the GPU working set at **~110 GB** by default → model sits at **92%** with no
room for KV cache → timeout. FIX: `sudo sysctl iogpu.wired_limit_mb=122000` (122 GB → ~20 GB headroom).
Made permanent via a LaunchDaemon: `dist/install_gpu_limit.sh` + `dist/com.glm52.gpulimit.plist`
(installed, `launchctl`-registered, survives reboot). Added to the model card as a **required** setup
step — without it, downloaders think the model "randomly crashes". Single best stability fix of the project.

## Speed: the deep investigation (2026-06-17) — measured the easy wins DEAD (the gold)
Baseline **11.3 tok/s** (no draft) — abnormally low vs comparable 4-bit MoEs on M5 Max (Qwen-122B-Q4
~65, DSV4-70B-4bit ~32). 6 web-research rounds + 2 microbenchmarks (`scripts/70_profile_decode.py`,
`scripts/71_profile_experts.py`). **The measurements OVERTURNED the research** — twice:
- **❌ 4-bit re-quant = SLOWER for decode.** Microbench `70`: 3-bit **158 µs**/matmul < 4-bit **220 µs**
  (0.72×). Single-token decode is BANDWIDTH-bound → smaller (3-bit) wins. The web's "4-bit faster" is
  PREFILL/compute (optimized kernel, big batches), NOT our decode. A 4-bit re-quant would've HURT speed.
- **❌ Active-experts 8→4 = NO win** at batch=1. Microbench `71`: top-4 ≈ top-8 (small-batch GPU
  underutilization; fixed per-call overhead dominates). Matches the web's ~5-8%. Not a real lever.
- **Root cause of the 3× gap = MLX's NAIVE DSA implementation**, not our architecture. mlx-lm **#837**
  "DeepSeek V3.2 has multiple issues"; mlx **#3402** "0.27 tok/s is a STRUCTURAL hard floor"; DSA decode
  uses a "naive SDPA path — production GPU kernels are significantly faster". **A chunk of our slowness
  improves FOR FREE as MLX matures.**
- **The REAL levers, in order:** (1) **`--dsa-block-size` 32/64/128** — free serving-flag sweep, the one
  stone unturned (queued in the proof's STAGE F). (2) **Upstream MLX DSA kernels** (track #837/#3402) —
  free over time. (3) **MTP self-speculative ~2.6×** — the only thing that beats the bandwidth wall
  (read once, emit N tokens), but a PORT for GlmMoeDsa: MTPLX is Qwen-only, mlx-lm MTP PR **#990** has
  "no GLM5". Path: recover the MTP head from the kept **381 GB mxfp4** (it HAS it,
  `num_nextn_predict_layers=1`) OR train an EAGLE-3 head on our activations (1-3B, no target finetune).
  (4) 2-bit experts = faster (less data) but quality cliff ("below Q4, MoE falls off a cliff").
- **⚠️ KEEP `models/GLM-5.2-mxfp4` (381 GB)** — it holds the MTP head for the speed work. Safe to delete:
  the v2 lineage (`pruned-v2` + `q3-v2` + `q3a4-v2` ≈ 319 GB, superseded by v4).
- **Lesson: MEASURE, don't just research.** 6 rounds of blogs confidently said "4-bit"; a 30-second
  microbench killed it. The easy speed wins were mirages — measurement saved a multi-hour re-quant
  that would've made decode *slower*.

## Community scan on HF (2026-06-17) — we're UNIQUE + validated; speed is NORMAL (correction)
- **We're the ONLY 128 GB-fit GLM-5.2.** Every published MLX quant is the FULL model needing 512 GB–1 TB
  RAM (pipenetwork 4-bit 430 GB / mixed-3·6bit 360 GB; inferencerlabs 4.8-bit). REAP-pruned GLM-5 exists
  (0xSero, 50%, GGUF/GPU) — we pruned harder (70%) for Mac. **The demolition IS the differentiation.**
- **Our quant is validated:** pipenetwork uses the same `experts@3-bit affine g64`. (They use attn@6-bit; we use 4-bit.)
- **Speed CORRECTION (I'd over-claimed "3× abnormally slow"):** 11.3 tok/s is NORMAL. The reference
  inferencerlabs 16.6 is on **M3 Ultra (~800 GB/s)** vs our **M5 Max (~512 GB/s)**; the "Qwen-122B 65 tok/s"
  ref is **3B-active** vs our **~37B-active**. Hardware- and active-param-normalized, we're in line. The
  DSA-kernel overhead is **shared by ALL** GLM-5.2/DSV3.2 MLX users — not us doing something wrong.
- **Future QUALITY refinements (not speed):** **attn@6-bit** (pipenetwork) for attention fidelity;
  **dynamic-quant DQ3** (mlx-community DQ4plus reports "DQ3 ≈ 4-bit quality") for better 3-bit at our size.

## Speed REFRAME (2026-06-17) — for AGENTIC use, PREFILL not decode is the bottleneck (the real win)
11.3 tok/s decode is the WRONG number to chase for our use case. Coding agents send dozens of calls with
a shifting/growing prefix; mlx_lm.server INVALIDATES the KV cache on prefix shift → re-processes the whole
context every step → 30-90s/response (a 40K-ctx prefill ≈ 200s vs ≈5s cached). The REAL wins:
- **Prompt caching (prefix-aware) — up to 9.7× faster TTFT.** Turns 30-90s/agent-step into 1-3s. **#1 win.**
- **TurboQuant KV-cache quant** — decode stays FLAT as context grows (plain MLX 83→13 tok/s; TurboQuant
  ~95-110, 5× KV compression, identical output). Critical for long sessions. MLX port: arozanov/turboquant-mlx.
- **Better engine (drop-in OpenAI):** Rapid-MLX ("4.2× vs Ollama, 0.08s cached TTFT, supports GLM, 17 tool
  parsers, prompt cache, reasoning separation; works w/ Claude Code/Cursor/Aider"), oMLX (SSD-paged KV for
  agents), MetalRT (1.10-1.19× decode vs mlx-lm, same files), vllm-mlx (continuous batching 3.4× concurrent).
- **⚠️ CAVEAT:** must verify they load `glm_moe_dsa` + our 3-bit quant (needed a custom patch in mlx-lm). TEST,
  don't assume — but it's swapping a server, not porting a kernel (far less work than MTP).
- **Corrected priority:** prompt-cache + KV-quant (prefill, agentic) > dsa-block-size (free decode) > MTP
  (decode 2.6×, hard). For agentic coding the prefill win DWARFS the decode win — we'd been chasing tok/s.

## Community gems to ADOPT (2026-06-17) — Cerebras calibration recipe + eth-sri verified decoding
Deep HF/repo dive found two directly-actionable upgrades (others do PIECES of our stack; nobody the whole):
- **Cerebras REAP (the authors!) calibration data mix** — validates + polishes our v4 "code-first balanced":
  24,576 samples @ 16K seq = evol-codealpaca-v1 (4096 coding) + open-r1/Mixture-of-Thoughts (12288, **EQUAL
  code/math/science** — the math-super-expert protection we found the HARD way in v3→v4) + xlam-function-
  calling-60k (4096 tool) + SWE-smith-trajectories (4096 agentic). **ADOPT for any future re-prune** (richer
  than ours + adds tool/agentic). Repo: `CerebrasResearch/reap`, `experiments/pruning-cli.sh`.
  - `renormalize_router_weights` (+0.7% cleaner prune): we **LIKELY already have it** — `23_stream_calibrate.py`
    uses the model's real gate scores (`contrib=scores*norms` line 132, same `scores` as forward line 140), so
    if `norm_topk_prob=True` (standard DSV3.2) we inherit it. CONFIRM norm_topk_prob to be sure.
  - `SINGLETON_SUPER_EXPERTS`: force super-experts into singleton clusters so they survive the prune (cites
    the Super-Experts paper 2507.23279 we referenced for the math collapse). A protection worth adding.
  - Cerebras publish REAP-GLM (GLM-4.6 / 4.7-Flash) — validates our method; we did 70% + Mac + heal + agent.
- **eth-sri type-constrained decoding (PLDI'25) — upgrade verified-decoding (#21) from line-level → TOKEN-level:**
  `typesafe_llm.sampling.sample_constrained` + incremental `parse_ts_program` mask ill-typed tokens BEFORE
  sampling (correct-by-construction, "compile errors halved"), TS-only for now. + **IterGen (ICLR'25)**
  KV-cache-reuse backtracking — pairs with our new `src/prompt_cache.py` KV machinery. Repo:
  `eth-sri/type-constrained-code-generation`. Ours is line-level check-and-backtrack; theirs is stronger.
- **Uniqueness CONFIRMED:** nobody demolishes a 743B frontier model for a laptop — the local crowd runs small
  NATIVE MoEs (Qwen3.6-35B-A3B, North Mini Code 30B; faster, 50-90 tok/s). Our demolished-frontier-specialist
  bet is ours alone. The comparison to run eventually: us vs a native 30B coder, in-niche.

## Capability frontier + M5 Max 128GB research (2026-06-17) — new lanes found
- **Self-Trained Verification (arxiv 2605.30290) — THE find (→ task #26):** train the generator to incorporate
  verifier feedback → it writes correct code NATIVELY, even without verification at test time. We do this for
  math (RFT, `65`). EXTEND to ALL verifiers (compile/lint/SQL/Lean/design) → the verifier mesh becomes a
  self-improvement FLYWHEEL that lifts native ability, not just a runtime gate. The deepest verify-everything play.
- **Continual Harness (Princeton, Karten et al., May 2026):** an agent that compounds learning in one unbroken
  run (never restarts). Strategic direction for our own-your-repo + skill library + flywheel → a private
  specialist that improves the more YOU use it (cloud structurally can't). [[glm52-demolition-project]] moat.
- **Newer MoE compression (future re-prune, beyond REAP):** M2M-DC (mutual-information-guided prune + staged
  distill), EvoESAP (non-uniform per-layer pruning — we prune ~uniformly), CAMERA (micro-expert redundancy).
  REAP accepted to ICLR 2026; prune→quant→distill recipe validated (ours).
- **M5 Max 128GB specifics:** bandwidth **460-614 GB/s** (our 11.3 tok/s rides this — bandwidth-bound confirmed).
  Memory TRADEOFF: our 99GB model leaves ~23GB free at the 122GB limit → KV/context is TIGHT vs a 40GB model
  with 88GB context headroom. **KEY: TurboQuant KV (5× compression) is a CONTEXT-CAPACITY unlock, not just
  speed** — it lets the tight KV budget hold ~5× more agentic context (whole-repo context for the agent).
  Reframes the TurboQuant item in #25. QLoRA heals confirmed feasible (quantized model → auto-QLoRA, hours-scale).
  NVFP4 fast on M5 Max (Qwen-35B decode 58→112) but not turnkey for glm_moe_dsa. Plug in (60-90W, fans @ 2-3min).

## Session 3 (2026-06-17 eve) — stability + formal-math PROVEN + the custom-MLX engine
The verify-everything thesis, proven end-to-end & fully local. Modules built + selftested: `stability.py`,
`serve_stable.py`, `constrained_decode.py`, `self_heal.py`, `prompt_cache.py`, `66_prove.py`, `67_lean_expert.py`.
- **Formal math 5/5** (PhD-math Phase 1+2): healed GLM-5.2 on 4K Lean rows → `adapters-lean`; `verify_lean`
  (Lean 4.31.0) accepts-true/rejects-false; `66_prove.py` (best-of-N + verifier-guided self-correction) →
  **5/5 theorems Lean-VERIFIED** (2/5 pass@1 → 5/5 with correction). Phase 2 `67_lean_expert.py` = the self-heal
  flywheel on Lean. Recipe + improvements in PHD_MATH_PLAN.md; [[glm52-formal-math]] memory.
- **Serving stability** (#47): long-run crash = mlx-lm **#883 unbounded-KV → kernel panic** (wired mem, Jetsam
  can't reclaim). FIX = `src/stability.py` (8 components): **`mx_set_limits`** (MLX-native evict-not-crash),
  **`serve_stable.py`** (held across ALL proof runs, zero crashes), watchdog + `resilient_call` (wired into agent 57),
  circuit-breaker, subprocess-lifecycle, checkpoint. [[glm52-stability]] memory.
- **Custom-MLX engine** (#32-46): ONE constrained-decoding sampler (`src/constrained_decode.py`, selftested) →
  correct-by-construction across **color** (OKLCH+WCAG), **design** (scale/grid), code (type), math (Lean), SQL
  (schema), agent (secrets/test-tamper). + `self_heal.py` (compounds 0.50→0.84), `prompt_cache.py` — all selftested.
  Fused-MoE-kernel / MTP / batched / FIM tasked. "Constrain=correctness, steer=style, batch=search, speculate=speed."
- **Speed map** (saturated, [[glm52-speed-findings]]): 4-bit & active-experts MEASURED-DEAD; real levers =
  dsa-block-size + MTP + prompt-cache (prefill 9.7×). **MLX-first principle** ([[mlx-first-principle]]): MLX-native everything.

## Model-designs-it result (2026-06-17) — honest design-capability finding
`scripts/69_model_designs.py`: the MODEL (not Claude) takes a design brief, writes the HTML/CSS, the
render-and-measure critic judges it, the model revises (3 rounds). Result: it produced a real 7.2 KB
page but **didn't fully pass** — 2 critic issues (used rgb/hex not OKLCH; no CSS Grid). Honest read:
**the model CAN design but isn't design-soul-elite yet** — v4 was healed on code+math, NOT the design
canon. This is exactly the gap the **design-canon heal** (`67_build_design_canon.py`, 1,200 rows) closes.

## Autonomous goal-push (2026-06-17 night) — harden + finish + research
Goal: finish pending items; when GPU-blocked (flywheel owns GPU), HARDEN built items + research.
- **Flywheel result (#28/#31):** Lean expert-iteration lifted pass@1 **2/5 → 4/5 (round 1) → 4/5 (round 2, PLATEAUED)**.
  The plateau is the documented expert-iteration saturation (sparse rewards; EvoCoT/STP). Levers researched +
  documented in PHD_MATH_PLAN: (1) STP conjecture-generation self-play [BIG], (2) self-evolving curriculum
  (WIRED: scaffold curriculum.jsonl now feeds forward in 67), (3) entropy/diversity, (4) failure-prefix
  conditioning, (5) filter-out-easy, (6) don't over-iterate (collapse risk).
- **Hardened (all selftest-PASS, GPU-free):** stability, constrained_decode, self_heal, prompt_cache, gen_primitives, rag.
- **Built:** `src/gen_primitives.py` (#35: FIM 4 schemes + best-of-N verify-selection). 8 constrained validators
  (#36-41,#45: color/design/algebra/art/sql/secret/test-tamper/tool) + CRANE best-practice (constrain output not
  reasoning — avoids the alignment/format tax). `src/rag.py` confirmed = #6 (BM25 zero-token retrieval) + selftest added.
- **Reach (#49-52):** generalized installer (#50, patches every mlx_lm); upstream PR prepped (#49, glm_moe_dsa.py +
  PR_glm_moe_dsa.md, closes mlx-lm #879); GGUF actionable via llama.cpp PR #19460 (#51); Swift port roadmapped (#52).
- **Resolved (done or research-decided):** #4,#6,#8(KD→RFT),#11,#13,#16,#18(GRPO regressed→RFT),#19(pruning won),
  #21,#24,#29,#30,#36-41,#45,#46,#47,#50.
- **GPU-blocked (flywheel running) / multi-day, honestly roadmapped:** heals #17/#23, quant #20/#12, TurboQuant #25,
  multimodal #42-44, kernels #33, MTP #10/#34, batching #35/#48, GGUF #51, Swift #52, PR-submit #49 (user action).

## ⚠️ The weights on disk + the MTP head (RECORDED — stop re-deriving this; DO NOT DELETE)
- `models/GLM-5.2-mxfp4` (381 GB) — mxfp4 original we prune from. **max layer 77 — mxfp4 convert DROPPED the MTP layer 78.**
- `models/GLM-5.2-q3a4-v4` (99 GB) — current pruned+quantized (also max layer 77, no MTP).
- `~/.cache/huggingface/hub/models--zai-org--GLM-5.2` — raw **BF16** original. Index lists layers 0..78 (HAS the MTP head)
  but **weights are NOT downloaded** (5.2 MB = index/config only).

**MTP/nextn head = layer 78** (config `num_nextn_predict_layers:1`): 791 tensors = enorm+hnorm+eh_proj+shared_head + a
full transformer block (self_attn + MoE). Powers self-speculative decode (~1.3-2x) per mlx-lm PR #990 / MTPLX.
**For #34:** the head is NOT usable on disk (mxfp4 dropped it; BF16 is index-only). Must DOWNLOAD layer-78 tensors
(~10 GB) from `zai-org/GLM-5.2` BF16, stream-quantize to q3a4, attach as layer 78 in glm_moe_dsa.py + draft→verify loop.
Extractor: `scripts/72_extract_mtp.py` (inventory works; `--extract` once weights present). Memory: [[glm52-originals-mtp]].
**DO NOT DELETE** models/GLM-5.2-mxfp4 (re-prune source) or the q3a4-v4 (current model).

## 🐛 FLYWHEEL COMPOUNDING WAS SILENTLY BROKEN (found + fixed 2026-06-17)
69_lean_flywheel.py sft() built its train data with `cat heal/lean/train.jsonl heal/lean-rft/train.jsonl > lean-fly`.
When the first file lacks a trailing newline, cat MERGES its last line into the next file's first → one malformed
JSONL line → mlx_lm lora dies with `JSONDecodeError: Extra data` → SFT fails → NO new adapter saved. run_with_lifecycle
swallowed the error, so the flywheel "completed" each round WITHOUT actually training. The measured [4,4]/[4] plateau
was an ARTIFACT — it kept re-evaluating the same start adapter (adapters-lean-v2), never the (never-created) rN adapter.
**Fix:** sft() now uses `_merge_jsonl()` — validate each JSON line + write proper newlines (same fix as the earlier
Phase-2 crash; it regressed). Verified: 3-iter SFT now "Saved final weights". The flywheel can finally compound.
LESSON: never `cat` JSONL; always validate-merge. And surface subprocess failures (don't swallow).

## Plateau-breaker A/B results (2026-06-17 ~22:45) — honest: inference-bias NEUTRAL, training-bootstrap is the lever
Two novel plateau-breakers for the 4/5 cold-start, both TESTED:
- INFERENCE logit-bias (deep-MLX, 66_prove --logit-bias): naive boost=8 → 3/5 (HURT — over-steered omega/simp onto
  the ∧ goal and_comm, breaking it). Fix = goal-conditional (goal_is_arithmetic: bias only +/*/≤ goals, not ∧∨→)
  → recovered to 4/5 (no harm) BUT did NOT break the plateau (0+n=n still fails — a logit nudge can't overcome the
  model's prior). VERDICT: neutral, correctly default-OFF. Honest negative — the test caught it.
- TRAINING bootstrap (66_prove.enumerate_tactics, wired into 67 gen): GUARANTEES the verified 0+n=n:=by omega proof
  (tested 5/5 pure-Lean) → seeds SFT so the model LEARNS the tactic. The sound lever; GPU test = the breaker flywheel.
LESSON: inference-time steering (logit-bias) ≠ teaching; the cold-start needs a real training signal, which the
enumerate bootstrap provides. Always A/B with the honest eval (breaker OFF) — a "novel idea" can regress.

## ⭐ CRITICAL: formal-math verifier was CAPPED (no mathlib) — found + fixed (2026-06-18, CPU-only)
verify_lean ran `lean <file>` standalone → NO mathlib → omega/simp/decide/rfl worked but positivity/nlinarith/
ring/field_simp (mathlib) ALL FAILED. So EVERY mathlib proof the model wrote was failed by the verifier → the
miniF2F run (~6%) is a severe UNDERESTIMATE, capped by our toolchain, not the model. FIX (CPU-only, no GPU):
created lean-verify/ project (lean-toolchain v4.31.0 + mathlib @ v4.31.0, `lake exe cache get` → 8516 precompiled
oleans, NO build), wired verify_lean to prepend `import Mathlib.Tactic` + run `lake env lean` inside the project.
TESTED: positivity/nlinarith/ring now verify ✓ (were ✗). The formal-math lane (#27-31 + flywheel) is UNCAPPED.
The current miniF2F run uses the OLD cached verify_lean (capped) = core-Lean baseline; a mathlib RE-RUN gives the
real number. Speedup TODO: import Mathlib.Tactic is ~10-30s/check; LEAN_REPL/persistent-server = ~5x faster (PHD plan).
LESSON: always validate the VERIFIER itself — a capped verifier silently understates everything downstream.

## ⭐ VERIFIER MESH AUDIT (2026-06-18, CPU-only) — found + fixed 2 silently-broken verifiers
Lesson from the mathlib cap: a broken verifier silently corrupts EVERY downstream result. So audited all 7
(good-input must PASS, bad-input must FAIL). Found:
- **verify_python BROKEN (critical):** `_py` called bare `["python", ...]`; when absent (venv has python3, not
  python), `_run` returns rc=-1 → `_result` treats -1 as SKIP=PASS → it passed ALL code incl. syntax errors.
  Every "verified" Python (best-of-N, code flywheel) could have been a FALSE pass. FIX: use sys.executable (_PY).
- **verify_lean CAPPED:** no mathlib (see prior entry) → mathlib proofs failed. FIX: lean-verify project.
- sql/js/ts/rust/go: confirmed honest (sql first looked broken but my test used a missing table — unfair).
RESULT: MESH 7/7 honest (python/sql/js/ts/rust/go/lean all good-pass + bad-fail). The verify-everything thesis
now stands on a verified foundation. LESSON: -1/skip-as-pass is a dangerous default — a missing toolchain should
be loud, not a silent pass. Audit verifiers with BOTH a good and a bad case, always.

## Premise selection (#31, the #1 lever 4%→20%) — research→test→IMPROVE→verify cycle COMPLETE (2026-06-18)
LeanSearch v2 (2605.13137): retrieval lifts proof success 4%→20%. Built it CPU-only over mathlib source:
- v1 BM25 (lexical): TESTED → NOT better. Goal `a²+b²≥2ab` shares 0 keywords with `sq_nonneg` → retrieved
  irrelevant jacobiSym/Fibonacci lemmas. Honest negative; did NOT ship.
- v2 SEMANTIC (fastembed bge-small→now bge-large, CPU): TESTED → BETTER. 4/8 algebra-relevant vs BM25's 0/8 on the same
  AM-GM query; "add comm" → add/commutativity lemmas. Upgraded PremiseIndex to semantic (BM25 fallback).
Wired into 66_prove via --premises (inject retrieved lemmas into the prompt). Default-OFF until a full-index
run validates the end-to-end lift. TODO: full mathlib index (~100K lemmas) embeds in ~10min → cache to disk;
ideally a Lean-trained embedder (LeanSearch) for best precision. LESSON: lexical retrieval fails on math —
semantics matter; and "test to verify it's BETTER" caught + fixed it instead of shipping noise.

## The Demolition family — shrink, keep the soul (2026-06-18)
Same masters-trained soul (8 facets), every size — facet-inclusive calib + heal corpus are size-agnostic.
Scripts: 79_demolition_family.py (build) · 80_family_eval.py (soul-retention scorecard) · 78_facet_calib.py.
```
 ~106GB: 77e·3bit (baseline, this model) →128GB    67GB: 46e·3bit →96GB Mac
   55GB: 36e·3bit →64GB Mac                        36GB: 26e·2.5bit →48GB Mac
   20GB: 16e·2bit ⚗️ →32GB Mac                      14GB: 8e·2bit ⚗️ floor(10.4GB base) →24GB Mac
```
Per size: facet-calib → saliency → prune harder → quantize → heal(soul corpus) → scorecard. Tasks #53-58.
