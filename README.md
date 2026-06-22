> ⚠️ **Describes an earlier version (v1: 3-bit / 99 GB).** Current = **v3: 4-bit / ~98 GB, HumanEval-164 = 69%, now PUBLIC** (https://huggingface.co/philipjohnbasile/GLM-5.2-Demolition-q4a4-soul-MLX, MIT). Canonical truth: `MODEL_CARD_v3.md` + `MISSION_SUMMARY.md`.

---
license: mit
base_model: zai-org/GLM-5.2
base_model_relation: quantized
library_name: mlx
pipeline_tag: text-generation
language: [en]
tags: [mlx, moe, code, agentic, glm, pruned, quantized, verified-decoding, apple-silicon, local-agent, conversational, soul, design, security, multi-domain]
datasets:
  - open-r1/Mixture-of-Thoughts
  - open-r1/OpenR1-Math-220k
  - open-thoughts/OpenThoughts-114k
  - HuggingFaceH4/ultrachat_200k
  - theblackcat102/evol-codealpaca-v1
  - Salesforce/xlam-function-calling-60k
  - glaiveai/glaive-function-calling-v2
  - SWE-bench/SWE-smith-trajectories
  - internlm/Lean-Workbook
---

# GLM-5.2-Demolition — a 743B frontier MoE on a 128 GB Mac, with a masters-trained soul

![One on-device base, a masters-trained soul, and swappable code specialties — on Apple Silicon](ai-engineer.png)

**One line:** we took `zai-org/GLM-5.2` (743B-parameter Mixture-of-Experts, ~381 GB at 4-bit) and
**demolished** it — *soul-targeted* expert pruning + **4-bit** quant (v3, `q4a4-soul`) — to **~98 GB** so it runs
**fully on-device on a MacBook Pro M5 Max (128 GB)**, then healed a **pure vanilla-code core** plus a **library
of swappable heritage "souls"** (each trained on the actual masters of a field), wrapped in a verifier-first
local agent that does what a cloud model structurally can't: the **compiler steers every line it writes**, it
**re-verifies tests on `done`**, and it **blocks known-format secret writes**.

It is **one ~98 GB pure-code base + a growing library of swappable, masters-trained souls** — a small
**model factory** on a single Mac. *(v1 was 3-bit/99 GB; v3 re-prunes from the original to 4-bit, MLX's sweet
spot, and keeps the experts that serve our facets — "soul-targeted" pruning.)*

## The shape: a PURE core, swappable souls

```
PURE CORE  (vanilla, always-on — no frameworks)     SWAPPABLE SOULS  (mount on demand — the factory)
└─ the FOCUS-9 languages, done excellently:         ├─ design · art · music · perfumery
   Python · TypeScript · JavaScript · Rust · Go      ├─ science · legacy · security (purple-team)
   HTML · CSS · SQL · Postgres                ×      ├─ gamedev (vanilla, from-scratch) · fullstack
                                                     └─ math · dataviz · prose · architecture · research
```

- **Why pure:** the core is *just the vanilla languages* — no React/Django/Unity/frameworks, no baked
  specialties. Everything applied is a **soul** you mount per-request. Keeps the core sharp and universal.
- Each **soul** is a small LoRA that *names a field's masters* to activate latent eliteness — Basquiat/Banksy/LeWitt
  (art), Bach/Dilla/Eno (music), Carmack/Handmade-Hero (gamedev), Saltzer-Schroeder/Aleph-One (security),
  Rams/Bauhaus (design), K&R/Knuth/Dijkstra (legacy), Beaux/Guerlain/Ellena (perfumery), Feynman/Darwin (science).
- The **base** (~98 GB, 4-bit soul-targeted) is built once from the original — the expensive part (prune + quant 743B).
- The **soul** is a small (~500 MB) LoRA that makes the model *elite* — not just correct — at every facet,
  trained on gold spidered from the people who *defined* each field (Rams/Müller-Brockmann for design,
  Kernighan/Knuth for code, Erdős/Pólya for math, Tufte for dataviz, Saltzer-Schroeder for security,
  Strunk/Orwell for prose, Parnas/Uncle-Bob for architecture, Feynman/Popper for research).
- The **code module** is a swappable ~500 MB adapter: a game dev and an AI engineer load the *same* elite
  design/prose/math/security — only the coding expertise changes. New market = one small adapter, not a new base.

## The soul, and how it's built
The demolished base reverts to the *average* of its training. To make it **elite**, we don't ask it to
imitate itself (that degenerates) — we **research the masters** and heal toward them:

> **spider the elite canon of a field → generate audit-gated, secure-by-default gold → heal a LoRA → scorecard**

The current core soul (`adapters-soul2`) is **250 masters-grounded examples across 8 facets** — every one
`json.dumps`-clean, gated by a per-facet eliteness audit (with a degeneration guard), and **secure-by-default**
(parameterized queries, AEAD crypto, no hardcoded secrets, validated input). The heal **preserved code**
(HumanEval held at 116/164 = 70.7%, identical to the prior soul) while adding the full facet breadth.

**Design ranges from restraint to maximalism** — Swiss minimalism (Rams · Müller-Brockmann · Vignelli) *and*
pop-street (Warhol · Banksy · Mr-Brainwash · Murakami), plus Bauhaus, editorial, product-systems, and
experimental/brutalist movements. **Security is full purple-team** — defensive core (crypto/web/net/secure-coding/
blue-team) **and** authorized red-team/pentest/CTF (every offensive technique paired with its detection +
hardening). **Math** spans Furstenberg → Ramsey → Zagier with Lean-4 proofs. Everything uses **current versions**
(React 19 · PyTorch 2.x · OWASP 2025 · CVE-2025 · Java 21 · PHP 8.4) — *except* the legacy module, which is
intentionally old (and also carries the modern target: COBOL-on-Kubernetes, Spring Boot 3, .NET 8).

## How it was made
1. **Pruned** the MoE experts 256 → 77 by **router-weighted saliency (REAP** = `router_weight ×
   activation_norm`, padding-masked), streaming layer-by-layer (~5 GB working set — it never fits in RAM).
2. **Quantized** mixed-precision (MLX): experts **3-bit**, attention/embeddings/lm_head **4-bit** → **99 GB**.
3. **Healed** with **LoRA SFT** (`--no-mask-prompt`, grad-checkpointed, **`--max-seq-length 2048`** — above that
   GLM-5.2's DSA sparse-attention scatter is non-differentiable and the backward crashes). A **code-first
   balanced calibration** keeps the *math* super-experts alive through the prune; the **soul** heal then makes
   it elite across all facets. *(GRPO/RLVR was tried and regressed → SFT.)*

## What makes it different (built + selftested)
- **Verified decoding (compiler-steered):** generates line-by-line while the **real type-checker runs in
  the loop**; a line that adds an error is backtracked. TS 0.3 ms · Python ~0 ms · Rust 34 ms per check.
  Practical *only* on Apple Silicon — unified memory lets the model (GPU) and compiler (CPU) share RAM.
- **The verifier mesh:** every output meets its real tool — compile+run+**idiomatic lint** (clippy/ruff/
  gofmt/prettier) for 5 langs, **SQL** (sqlite), **math** (SymPy), **proofs** (**Lean 4**), design (render+see).
- **A 51-tool agent** with **five defense layers** the frontier lacks out of the box: trust (checkpoint/rollback,
  secret-scan, prompt-injection guard, audit, risk-gate), reliability (constraint-pinning, false-success guard,
  flaky-test re-run), self-improvement (skill library, clarify-before-assuming), integrity (test-tamper guard,
  fabrication-proof `done`, slopsquat guard), plus a **humanizer** (kills AI-slop, matches your voice).
- **Own your repo:** `scripts/64_own_your_repo.py` fine-tunes on *your* private codebase — a cloud flagship can't.
- **Design soul** (render-and-measure critic: WCAG/type-scale/OKLCH), **CallSieve** zero-token retrieval +
  live-docs RAG, **vision/voice/video** (all MLX), code-rendered math/arch figures (matplotlib/manim/TikZ).

## Features — everything that's built
The bet isn't "highest SWE-bench" — it's **the most reliable** local agentic coder, elite across the whole stack.
Every item below is **built + selftested** (not roadmap; the roadmap is its own section). Receipts live in the linked docs.

### The demolition
- **743B → 99 GB.** `zai-org/GLM-5.2` (743B MoE, ~381 GB at 4-bit / ~1.5 TB bf16) demolished to **99 GiB at q3a4**
  (experts **3-bit**, attention/embeddings/lm_head **4-bit**) — runs **fully on one 128 GB M5 Max**.
- **REAP prune 256 → 77 experts** by router-weighted saliency (`router_weight × activation_norm`, padding-masked),
  streamed layer-by-layer (~5 GB working set — it never fits in RAM).
- **NVFP4 re-quant wired** (`24b_stream_requantize --nvfp4`, `04b --bit-choices`) — half the 3-bit error and the
  M5 2× hardware path; the **#59** saliency-dynamic quant prep is in place behind the factory.

### The agentic-reliability moat
- **51-tool ReAct agent** with trajectory compaction + stall detection for long-horizon runs.
- **Grammar-constrained tool-JSON** — invalid tokens get zero probability at each step, so a malformed tool-call is
  **structurally impossible** (vs the field's best: "fewer malformed"). Speaks 2026 strict-schema + MCP conventions.
- **Verified / compiler-steered decoding** — the real type-checker runs in the loop and a line that adds an error is
  backtracked **as it's written** (TS 0.3 ms · Python ~0 ms · Rust 34 ms per check).
- **Fabrication-proof `done`** — the agent **re-runs the original tests** before claiming success; it can't hallucinate a pass.
- **Integrity layer** — test-tamper guard, **16-provider secret-scan**, scope enforcement, slopsquat guard.
- **The verifier mesh** — every output meets its real tool: compile+run+idiomatic-lint (clippy/ruff/gofmt/prettier) for
  **5 langs**, **SQL** (sqlite), **math** (SymPy), **proofs** (**Lean 4**), and a **design render-critic** (render+see).

### Multi-tier M5 Max hardware use (every tier earns its keep, in parallel)
- **GPU** — decode + NVFP4 + image-gen.
- **CPU (18 cores)** — runs the whole verify-everything stack in parallel: `verify_many` fans the verifier mesh across
  all 18 cores (**measured 6.6×**) and feeds proof-search.
- **ANE (16-core Neural Engine)** — embeddings via Apple `NLContextualEmbedding` (`src/ane_embed.py`, `backend=ane`,
  no coremltools): **768-dim, ~9.5 ms**, verified.
- **SSD** — warm-start **prompt-cache persistence** (`save()/load()` + keyed warm-start; round-trip selftest PASS).

### Breadth — the 10-facet soul
- **One always-on soul** makes the model *elite*, not just correct, across **design · dataviz · prose · math ·
  research · architecture · security (purple-team) · science · perfumery** — trained on master-grounded gold,
  per-facet eliteness-audited, secure-by-default, with code preserved (HumanEval held at **116/164 = 70.7%**).
- **Formal-math Lean prover** (`66_prove`) — local Lean-4 prover lane: **miniF2F-test 32/226 = 14.2% pass@4**,
  **Lean-verified**, contamination-checked.

### Multimodal stack (all MLX)
- **Vision** (Qwen3-VL-4B-8bit), **image-gen**, **video**, and **structured tools** — plus code_intel across 5 langs.

### The model factory
- **Swappable domain adapters** on one base (download once): each capability is a ~500 MB LoRA. **Pattern A =
  base + module gold** (a game dev and an AI engineer share the *same* elite soul; only the code module swaps).
- **Shipped souls:** **soul2 ✓** and **soul-v3 ✓** (on HF); `heal_queue.sh` driver is autonomous.
- **In the heal queue:** `fullstack` (healing now) → `gamedev` → `legacy` → FACTORY_DONE.

## Requirements
- **Apple Silicon, 128 GB** unified memory (M5-class recommended), macOS 26/27+. **MLX ≥ 0.31.**
- The architecture (`glm_moe_dsa`: MLA + DSA sparse attention) needs the **bundled patch** (`glm_moe_dsa.py`
  + `install_glm_dsa_patch.py`) — current stock mlx_lm can't load it. **Native support is landing upstream**
  ([ml-explore/mlx-lm PR #1410](https://github.com/ml-explore/mlx-lm/pull/1410)); once it merges, recent mlx_lm
  loads with **no patch**.
- **⚠️ Raise the GPU memory ceiling — required.** The model needs ~101.6 GB; macOS caps the GPU working set at
  ~110 GB by default, so it OOM-crashes on long generations. Fix before serving:
  ```bash
  sudo sysctl iogpu.wired_limit_mb=122000        # 122 GB; one-shot (resets on reboot)
  sudo bash dist/install_gpu_limit.sh            # OR: persist it via a LaunchDaemon
  ```

## Use it
```bash
python dist/install_glm_dsa_patch.py          # patch mlx_lm (venv AND LM Studio's bundled engine)
# serve the base + the soul (the swappable adapter is how you pick the specialty):
GLM_STREAM_EVAL=0 python -m mlx_lm.server --model models/GLM-5.2-q3a4-v4 \
    --adapter-path adapters-soul2             # the masters-trained core soul
# query it — enable_thinking toggles the reasoning trace (off = faster, on = harder problems):
curl -s localhost:8080/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Write a typed debounce in TypeScript."}],"chat_template_kwargs":{"enable_thinking":true}}'
# drive the 51-tool agent on your repo:
python scripts/57_tool_agent.py --repo /path/to/your/repo --apply --task "..." --test "cargo test"
```
In **LM Studio**: run the patch, fully quit + reopen, then load the model. **Speed:** single-stream is
memory-capped at ~11–14 tok/s — ALL speculative methods measured-DEAD on this MoE (see `SPEED.md`); throughput = batching.

## Performance (M5 Max 128 GB)
| Metric | Value |
|---|---|
| Size | 99 GiB / ~106 GB (from 381 GB mxfp4 / ~1.5 TB bf16) |
| HumanEval pass@1 | **116/164 (70.7%)** — full benchmark, single-shot, hidden-test scored; **held across the soul-v2 heal** |
| Math GSM8K | **8/12 (66%)** — small held-out subset; note: the verbose-CoT model needs a tighter answer-parser for the full set |
| miniF2F-test (formal proof) | **32/226 (14.2%)** — pass@4, Lean-verified, contamination-checked; a general model, NOT a specialized prover |
| Algebra (SymPy-checked) | **3/4 (75%)** |
| Decode speed (single-stream) | **~11–14 tok/s** — the memory floor; on MLX's *optimized* path already (gather_qmm + M5); MTP self-spec re-opened + measuring ([SPEED.md](SPEED.md)) |
| Batched throughput | **2.6× at B=8** (15.8→41.1 tok/s) · 1.74× at B=6 on the live serve — concurrent requests batch natively |

**Speed in one line (re-mapped June 2026, web-verified):** single-stream is **~11–14 tok/s**, and we're *already* on
MLX's optimized path (`gather_qmm` + the M5 Neural Accelerators — 11 tok/s is genuine, not a misconfig). EAGLE /
prompt-lookup / dsa-block-size were measured-dead, but **MTP self-spec is re-opened** — our accept-rate gate
(`89_mtp_gate.py`) is built and measuring now (honest expectation ~1.1–1.5× on a quantized MoE, *not* full-precision's
2.6×). The proven win remains **batching: a measured 2.6× throughput**, native in `mlx_lm.server`. Receipts: [`SPEED.md`](SPEED.md).

> **★ Why this is special vs the whole field** — a model the ecosystem treats as 8×H200 / 376 GB-Q4 territory, running
> at 99 GB on one Mac, self-healing from real (un-gameable) verifiers: **[`research/WHAT_MAKES_US_SPECIAL.md`](research/WHAT_MAKES_US_SPECIAL.md)** (cited, June 2026).

**Benchmark honesty:** HumanEval is the **full 164** (116/164 = 70.7%, single-shot); GSM8K (**n=12**) is a **small
held-out subset**; miniF2F **is** the full 226. Every number is **contamination-checked** (0% / 0% / 0.4% near-dup) —
**reasoned, not memorized**. Honest frontier-vs-us comparison + projections: [`BENCHMARKS.md`](BENCHMARKS.md).

## The factory — swappable souls & code, one base
The spider→gold→heal recipe is **domain-agnostic**: "make a model elite at X" is now a repeatable procedure.
On the one 99 GB base (downloaded once), each new capability is a ~500 MB adapter:
- **Core soul** — design · dataviz · prose · math · research · architecture · security (purple-team) · science · perfumery.
- **Code modules (swap one)** — `fullstack/AI-eng/DS-ML` (RAG, agents, MLOps, deep-learning, data-eng, web/devops) ·
  `game/app` (Unreal C++/Blueprints, Unity C#, Godot GDScript, Flutter/Dart, Nystrom patterns, shaders, netcode) ·
  `legacy` (COBOL/mainframe, enterprise Java, PHP — classic **and** modernized to Java 21 / PHP 8.4 / .NET 8 / COBOL-on-K8s).
- Verified by design: each code module's gold targets a **compile-verification** pass (the leap Lean gave miniF2F).

**Swap a module + build a new specialty:** full mechanics — runtime swap · the two soul-merge patterns ·
the spider→gold→heal recipe · the rules — are in [`FACTORY.md`](FACTORY.md). The model is also being taught
its *own* factory (route a task → the right module, emitting a `<module>…</module>` signal), so it can self-select the specialty.

## Roadmap — what's queued next
Honest queue (the live kanban is `BACKLOG.md`). These are **not built yet** — the Features section above is:
- **ANE vision (#79)** — move the vision encoder onto the Neural Engine (the big ANE win; convert-friendly model).
- **ANE speech (#87)** — Whisper / `SFSpeechRecognizer` on the ANE — a voice lane.
- **SSD-backed long-context KV (#86)** — KV offload to the 14.5 GB/s SSD for long context (attacks our weakest axis
  vs 1M-ctx rivals; the #85 prompt-cache plumbing is already done).
- **Metal-4 TensorOps fused-MoE kernel (#81)** — custom fused kernel, the new M5 decode lever (**~30–60% decode**,
  `research/mlx_speed_deepdive.md`); distinct from the (dead) speculative methods.
- **#59 NVFP4 collapse-fix** — saliency-dynamic quant (early/late experts at 4-bit) to cure long-gen Computation Collapse;
  tooling is wired, GPU-gated behind the factory.
- **Agentic-gold heal (#84)** — heal the 23 staged agentic-gold examples into the soul.

## Roadmap — the Demolition family (shrink, keep the soul)
Same masters-trained soul, every Mac — the elite training lives in the size-agnostic calibration + heal corpus:
```
 ~106GB : ████████  77 experts · 3-bit   (this model)   → 128 GB Mac
   67GB : ██████    46 experts · 3-bit                   → 96 GB Mac
   55GB : █████     36 experts · 3-bit                   → 64 GB Mac
   36GB : ███       26 experts · 2.5-bit                 → 48 GB Mac
   20GB : ██        16 experts · 2-bit  ⚗️                → 32 GB Mac
   14GB : █          8 experts · 2-bit  ⚗️ (the floor)    → 24 GB Mac
```
Sizes **measured** from the build: **~10.4 GB fixed base** + experts × ~1.24 GB × bits/3. The base dominates,
so **below ~13 GB is impossible** — the right column is your **minimum Mac RAM**.

## Honest limitations
- **Specialist base:** ~70% of experts pruned — strong in the trained facets, weaker on long-tail trivia. Not the full 743B.
- **Speed ~11–14 tok/s decode — the memory floor.** Every speculative lever was benchmarked and is dead here
  (proven 4 ways — [`SPEED.md`](SPEED.md)): MTP **0%**, external/prompt-lookup draft **0.32×**, dsa-block-size **flat**.
  The real "faster" is **throughput via batching (2.6× at B=8)**. A fresh EAGLE-3 head is the only single-stream path and is **not** recommended.
- **Raw single-shot arithmetic** is the weak spot (the model reasons *very* verbosely on math) — its **structured/formal**
  math (miniF2F via the Lean prover) is far stronger. The GSM8K subset needs a tighter answer-parser to measure cleanly.
- **The soul is a LoRA, not magic** — evaluate the per-facet soul-retention scorecard before relying on a facet; the
  swappable code modules (game/app, legacy) have their **gold built** and are **healing into adapters** (the factory's next output).
- **Multilingual** ability reduced (optional vocab-trim drops ~31% of tokens). Prompt-cache can OOM under heavy concurrent load.

## Attribution & license
**MIT.** Base model © **Z.ai** (`zai-org/GLM-5.2`, MIT-licensed) — so this derivative is MIT too: free
to use, modify, and redistribute **with attribution to Z.ai**. The demolition / healing / soul / 51-tool agent
tooling is this repo's contribution.
