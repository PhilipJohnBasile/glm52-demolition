# Implementation Plan — acting on the 9-round SOTA research (June 2026)

**Basis:** `research/swappable_adapters_sota.md` (9 deep rounds). Rounds 5–9 mostly *confirmed* our builds
(prune > merge, verifier-mesh over self-reward, on-policy distillation, MLX kernel-fusion, DSA top-2048,
contamination-checking) — the project is **SOTA-aligned**. This plan extracts the genuinely-new levers and
sequences them around the **single GPU**.

**Sequencing constraint:** one GPU. The **soul2 verdict** (GREEN — HumanEval held 116/164 — shipping via the
autonomous driver) goes first; GPU-bound work queues behind it. **GPU-free code changes happen now, in parallel.**

---

## TIER 1 — now (GPU-free / quick, highest value-per-effort)
1. **Overthinking fix** — a concise-CoT mode (reasoning-token budget + "think tersely, end with the answer"
   directive) in the serve / decoding path. **Why:** our 5–8K-token CoT *overthinks* — the 2026 literature shows
   that hurts accuracy + calibration, it's slow at 11–14 tok/s, and it's what broke the GSM8K answer-parser.
   **Test:** token-count drop + a clean final-answer extraction (no GSM8K-number-chase — just verify the parse).
2. **REAP logit-renorm fix** — renormalize the top-k router logits to sum to 1 in the prune script (the
   March-2026 / ICLR-2026 REAP update). **Why:** modest free accuracy gain on the next prune. Write now, runs later.
3. **CallSieve agentic-RAG upgrade** *(user-greenlit)* — expose **hierarchical retrieval as tools** (keyword +
   semantic + chunk-read, the A-RAG pattern) + iterative multi-hop, instead of one-shot fetch. **Look at the
   `callsieve` repo first** (separate checkout, `$CALLSIEVE_REPO`, default `~/git/callsieve`), then apply minimally.
4. **mlx-optiq probe** — `pip install mlx-optiq` + a load-test script (mount our q3a4 base + a rank-16 adapter,
   confirm per-request hot-swap). **Why:** it solves the factory's instant-swap (no 3-min reload). Validate when the GPU frees.

## TIER 2 — GPU-bound (queue behind the soul2 ship)
5. **soul2 ship** — in flight (driver; GREEN verdict). The new core soul.
6. **Saliency-dynamic quant (#59)** — protect the salient + structurally-sensitive experts and **early layers at
   4-bit+**, rest at 3-bit. **Why:** the design degeneration is **Computation Collapse** (round 4–5 diagnosis) —
   *only* fixable by mixed-precision on the critical experts, not decoding tricks. **The big quality win** (recovers design).
7. **Specialty heals** — the ~250 masters-gold examples (gamedev / legacy[old+modern] / cyber / pentest / science /
   perfumery / factory-router) → adapters, using **MoE-Sieve placement** (LoRA only the top-25% routed experts +
   attention → 70–73% smaller, more hot-swappable) + **iw-SFT** (importance-weighted curated SFT).
8. **KV-quant** (TurboQuant/KVQuant-style) — harden the serve against the 118 GB long-gen self-bound.

## TIER 3 — eval & quality
9. **Real-task benches** — weight FeatureBench / Terminal-Bench / LongCLI-Bench over the **saturating** SWE-bench (#62).
10. **Contamination-resistant eval** — LiveCodeBench / LiveBench (#66); our 0/0/0.4% near-dup checking is validated.
11. **Lean-OPD** (self-teacher critiques the student's Lean attempt) for the prover (#27–31); **agentic-RAG** for
    live-docs; **security** (LlamaFirewall / TRUSTDESC tool-poisoning guard + a "Zombie-Agent" check on the self-healing flywheel).

---

## First actions (this session)
- **Tier-1 #1 (overthinking)** and **#3 (CallSieve)** — GPU-free, start now.
- Queue Tier-2 (#59 saliency-quant, specialty heals) behind the soul2 verdict via the driver.
- The 2-bit BitNet family (#57–58) stays an *experiment* — BitNet needs QAT, our PTQ won't match it.
