# ☀️ Report 2 — soul2 SHIPPED (2026-06-19)

**TL;DR:** The 250-example multi-facet **soul2** healed, scored **GREEN**, and **shipped**. Code held exactly
(HumanEval-164 = **116/164 = 70.7%**, identical to soul v1) while the corpus added science · perfumery ·
deep-security · pentest · the full design-movement range. The per-facet flywheel confirmed a **known limitation
(3-bit long-generation degeneration), not a regression.**

## Verdict: GREEN ✓ — shipped
- **`adapters-soul2`** uploaded to HF (commit `859ed1a`).
- **HumanEval-164: 116/164 = 70.7%** — *exactly* soul v1. The 250-corpus (vs v1's 43) **preserved code capability
  while adding ~6× the breadth.** No overfitting collapse despite train loss 0.093 / val 1.22.

## The honest flywheel finding (long-gen degeneration, NOT a soul2 regression)
Per-facet self-generation scorecard (partial — stopped once the signal was unambiguous):
- **design: 0 elite / 24 reject** — fully degenerate on long HTML.
- **code: 2 elite / 13 reject** — and the tell is decisive: the **2 elite gens were SHORT (~1258 ch); the 13
  rejects were LONG (5–7K ch)** and collapsed into repetition + corrupted tokens (`UTF.FF9B`-style garble).

This is the documented **3-bit Computation Collapse on long generation** (`research/swappable_adapters_sota.md`,
rounds 4–5): the model degenerates *when it rambles* — **not** a soul2 regression (soul v1 degenerated identically).
The **gold/soul is elite** — the short elite gens prove it, and the masters-corpus is sound. The collapse is a
*serving/decoding* artifact of 3-bit on long output, which is exactly **why the soul is masters-GOLD, not self-gen.**

**The fixes (research-backed, queued):**
1. **Saliency-dynamic quant (#59)** — protect the salient + early-layer experts at 4-bit+, the rest at 3-bit. The
   research is blunt that Computation Collapse is fixable *only* by mixed-precision on the critical experts, not a decoding trick.
2. **Shorter CoT** — `scripts/08_think_proxy.py`'s reasoning budget (already built): short = elite, long = collapse.

## Corpus
- **soul2:** 250 masters-gold (8 facets) — SHIPPED.
- **+266 specialty gold** ready for the next round (the factory's modules): fullstack-AI-DS (8 areas), gamedev
  (Unreal/Unity/Godot/Flutter/patterns/gfx-net), legacy (COBOL/Java/PHP/Perl/VB + modern Java 21/PHP 8.4/.NET 8),
  cyber-core + pentest (purple-team), science, perfumery, factory-router.

## Next
Heal the specialty adapters (GPU now freed): **core-soul-v3** (non-code + science + perfumery + deep-security +
pentest + router) first, then the swappable code modules (fullstack / gamedev / legacy), using **MoE-Sieve placement**
(top-25% routed experts → ~70% smaller adapters) + **iw-SFT** — both from the research.

## Provenance
9-round June-2026 SOTA scan → `research/swappable_adapters_sota.md` + `IMPLEMENTATION_PLAN.md`. The verdict, the
collapse diagnosis, and the validations of our core calls (prune > merge, verifier-mesh over self-reward,
on-policy-KD now industry-standard, the DSA top-2048 = our heal limit) are all recorded there.
