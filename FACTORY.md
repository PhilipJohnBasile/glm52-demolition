# The Model Factory — swap a soul, build a specialty

One **~98 GB base** (v3: a 4-bit *soul-targeted* prune of GLM-5.2 743B — pure vanilla FOCUS-9 code) + small
**LoRA adapters**. Swapping the adapter swaps the capability; building one is a repeatable recipe — new market
= one small adapter, not a new base. The serve loads **base + exactly one adapter** at a time.

```
        ┌─────────────────────────────┐
        │  BASE  v3 (~98 GB, 4-bit)    │   ← pure vanilla FOCUS-9 code
        └─────────────┬───────────────┘
                      │  + ONE adapter (--adapter-path), mounted per-request
       ┌──────────────┼──────────────┬──────────────┐
   design/art/music   security       legacy         science/math/…
   (heritage souls)   (purple-team)  (old-fart)     (each = a canon + gold)
```

> **Honest measured caveat (2026-06-22):** the factory *pattern* is sound, but on this *demolished* base the
> soul adapters **don't lift** quality — gentle heals measure ≈ base, aggressive ones *degrade* it (see
> `MISSION_SUMMARY.md`). The demolished base is at its ceiling; the souls need a **clean right-sized base**
> (e.g. Qwen3-Coder-30B, which merle supports via `MERLE_BASE`) to actually pay off. The recipe + canons + gold
> all carry over to one — that's the up-path.

## 1. Swap at runtime (the mechanics)
The serve loads **base + exactly one adapter**:
```bash
# core soul (shipped):
GLM_STREAM_EVAL=0 python -m mlx_lm.server --model models/GLM-5.2-q3a4-v4 \
    --adapter-path adapters-soul2 --port 8080
# swap = stop, point --adapter-path at a different adapter, restart (~3 min model reload):
GLM_STREAM_EVAL=0 python -m mlx_lm.server --model models/GLM-5.2-q3a4-v4 \
    --adapter-path adapters-gamedev --port 8080
```
That's the whole swap. The adapter is the dial.

## 2. Two patterns — how the soul + the code half combine
This is the part people miss. A LoRA serve takes **one** adapter, so "elite soul × swappable code" can be built two ways:

| | **Pattern A — self-contained (today)** | **Pattern B — fused base (scaling)** |
|---|---|---|
| What | each adapter = soul + one code specialty, trained together | merge soul into the base once, then thin **code-only** adapters |
| Swap | change the whole ~500 MB adapter | change a ~100 MB code adapter; the soul is always-on |
| Pro | simplest; each adapter is fully self-sufficient | no soul duplication; smaller adapters; true "swap only the code" |
| Con | the soul is re-trained into every adapter (duplication) | one extra fuse step; base is now soul-specific |

**Pattern B fuse step** (when we scale): bake the soul into the weights, then train thin code adapters on *that*:
```bash
python -m mlx_lm.fuse --model models/GLM-5.2-q3a4-v4 \
    --adapter-path adapters-soul2 --save-path models/GLM-5.2-q3a4-soul   # base now has the soul
# then heal code-only adapters against models/GLM-5.2-q3a4-soul → swap just the code half
```
We're on **Pattern A now** (each specialty self-contained); Pattern B is the clean end-state once the soul stabilizes.

## 3. The autonomous chain (build the whole library overnight)
`scripts/factory_chain.sh` heals each specialty sequentially on the one GPU — *wait-for-GPU-free → heal → next* —
so the library forges itself unattended (~1.8 h/soul, render-checked so none crash mid-run). The chain:
**gamedev ✅ → legacy → security → fullstack → science → factory → perfumery**, each a swappable
`heal/adapters-<spec>` on v4.

The **`factory` soul is the meta-dispatcher** (`gold_factory/router.jsonl`): it teaches the model its *own*
architecture (99 GB MoE + swappable adapters) and to route a request to the right specialty itself — the
model-side counterpart of `src/omni.py` (the Any-to-Any router that dispatches across all 6 M5 chips).

**The soul library** (healed or healing): `soul2 · soul-v3 · soul-v4` (core / agentic) + `gamedev · legacy ·
security · fullstack · science · factory · perfumery` (specialties). Swap any with `--adapter-path heal/adapters-<spec>`.
A third option (from the research): **TIES/DARE-merge** soul + code into one adapter (base stays pristine) — see below.

> **This is a named field — and Apple ships it.** Our "factory" is the research area **MoErging / modular LLMs**.
> The per-request hot-swap (N adapters resident on one base, no reload) is **solved on MLX by [`mlx-optiq`](https://pypi.org/project/mlx-optiq/)**.
> **Apple Intelligence** ships this *exact* pattern on-device — a quantized frozen base + swappable per-task LoRA
> adapters + constrained "guided generation" + tool-calling. The full June-2026 scan — routing (Arrow / LORAUTER to
> 1500+ adapters), on-demand generation (Sakana Text-to-LoRA), merging (TIES/DARE), and cross-base transfer that
> gives the demolition family its adapters for free — is in [`research/swappable_adapters_sota.md`](research/swappable_adapters_sota.md).

## 3. Build a NEW specialty (the recipe — domain-agnostic)
"Make the model elite at X" is a procedure, not a research project:
1. **Spider the masters** — research agents read the elite canon of the field → `research/elite_<facet>.md`
   (the canon + *checkable* eliteness criteria). Don't imitate the model itself; it degenerates.
2. **Generate audit-gated gold** — agents write `heal/gold_<facet>/*.jsonl`: realistic prompt → elite answer,
   **secure-by-default**, **current versions** (except legacy), every record via `json.dumps` (never hand-written).
3. **Assemble** — dedup + shuffle → `heal/<corpus>/{train,valid}.jsonl`.
4. **Heal** — `python scripts/06_heal_lora.py --model models/GLM-5.2-q3a4-v4 --data heal/<corpus>
   --adapter-path heal/adapters-<facet> --iters 700 --max-seq-length 2048` → the adapter.
5. **Scorecard** — `scripts/77_soul_flywheel.py` (per-facet elite-rate) **+** `scripts/58_bench.py --n 164`
   (did HumanEval hold? — the regression guard). Green = ship.
6. **Ship** — `hf upload philipjohnbasile/GLM-5.2-Demolition-q3a4-MLX heal/adapters-<facet> adapters-<facet>`.

## 4. The rules (trip these and it breaks)
- **`--max-seq-length ≤ 2048`** on every heal — above it, GLM-5.2's DSA sparse-attention top-k scatter is
  non-differentiable and the backward pass crashes at step 1 (`scatter_axis VJP`). Inference is fine at any length.
- **`GLM_STREAM_EVAL=0`** for both serve and train (=1 stalls the serve and crashes training).
- **Audit every verifier with known-good *and* known-bad** before trusting it — verifiers false-pass silently.
- **Never fake a number.** A held-out scorecard or it didn't happen.
- **Raise the GPU memory ceiling** (`iogpu.wired_limit_mb=122000`) or long runs OOM.

## 5. The adapter library
| Adapter | Contents | Status |
|---|---|---|
| `adapters-soul2` | core soul v2 — design · dataviz · prose · math · research · architecture · security · code (250 masters-gold) | **shipped ✓** |
| `adapters-soul-v3` | core soul v3 — soul2 **+ science · perfumery · deep-security · red-team/pentest · self-swap router** (358 gold) | **healing** |
| `adapters-fullstack` | AI-eng/DS-ML code — RAG · agents · MLOps · deep-learning · classical-ML · data-eng · web · devops/test (60) | queued |
| `adapters-gamedev` | game/app code — Unreal · Unity · Godot · Flutter · patterns · shaders · netcode (47) | queued |
| `adapters-legacy` | legacy code — COBOL · enterprise-Java · PHP · Perl/VB — classic **and** modern (Java 21 · PHP 8.4 · .NET 8) (51) | queued |
| `adapters-soul` | the v1 soul (43 gold) | shipped (superseded) |

The swappable code modules (`fullstack` / `gamedev` / `legacy`) heal **GPU-serial** via `scripts/heal_queue.sh` — an
autonomous driver that ships each adapter on completion, then launches the next. The base + `adapters-soul2` runs
**today**; `adapters-soul-v3` is the next always-on core; each code module ships as its heal finishes. Each adapter is
self-contained (Pattern A): the proven soul base + that module's specialty gold. *Known limitation:* the 3-bit base
degenerates on very long single generations (the masters-gold is elite; the model just can't re-spin long output) —
the real fix is saliency-dynamic quant (protect the salient/early experts at 4-bit+), tracked separately.
