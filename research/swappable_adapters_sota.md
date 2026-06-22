# Swappable adapters / the "model factory" — SOTA as of June 2026

Deep-research scan of how the field does what we're calling the **model factory** (one base + a library of
swappable LoRA "souls/modules," the model self-routing among them). Bottom line: **we independently reinvented
a named, active research area — "modular LLMs / MoErging" — and the hardest part (hot-swap serving) is already
solved on MLX.** The factory is more buildable than first framed.

## 1. It has a name: **Modular LLMs / MoErging**
"MoErging" = **M**odel + r**E**cycling/**r**outing of experts. Independently-trained adapters accumulated into a
**library**, with a **router** that selects/composes them per input — exactly our "library of swappable souls."
- **Survey:** *A Survey on Model MoErging: Recycling and Routing Among Specialized Experts* (arXiv 2408.07057).
- **Canonical:** *Towards Modular LLMs by Building and Reusing a Library of LoRAs* (Ostapenko et al., ICML'24).
- Design axes the survey names — and where we sit:
  - **Expert source:** independently-trained, accumulated over time ✅ (our per-facet heals).
  - **Routing granularity:** example/task-level vs token-level. **Ours = example-level** (pick the code module per task) — cheaper, fits our case.
  - **Router:** learned vs **training-free** (see §2).
  - **Philosophy:** specialist vs generalist vs **hybrid** (generalist base + specialist plug-ins) — the survey flags hybrid as underexplored; **that's exactly our "core soul always-on + swappable code."**

## 2. The self-routing ("train it to swap") — 3 approaches, choose by library size
| Approach | Methods | When to add an adapter | Fit for us |
|---|---|---|---|
| **Training-free / zero-shot** | **Arrow** (routes via adapter weight SVD — no training), **PHATGOOSE** (post-hoc tokenwise gating) | **drop it in → instantly routable, NO router retrain** | **best** for an open-ended factory |
| **Learned dynamic** | **X-LoRA** (layer/token-level), **LD-MoLE** (2026, differentiable, adaptive #experts), **Glider** (instruction-driven global+local) | retrain the router | higher quality, more upkeep |
| **Retrieval** | **CARLoS** (retrieve LoRAs at scale), **LoRAHub** | embed task → retrieve adapter | **when the library gets large** (RAG-for-adapters) |

**Recommendation:** our **dispatcher gold** (the model emits `<module>game/app</module>`) is the simplest, most
transparent router and needs no extra infra — keep it. Add **Arrow-style training-free routing** as the automatic
fallback (so new specialties are routable without a retrain), and **CARLoS-style retrieval** once the library
outgrows a handful of modules.

## 3. The hot-swap serving — SOLVED, and on MLX
The thing I'd called a "Level-3 engineering task" mostly exists already:
- **CUDA/cloud:** **S-LoRA** (Unified Paging → 1000s of adapters/GPU), **vLLM** runtime LoRA load/unload
  (`VLLM_ALLOW_RUNTIME_LORA_UPDATING`, per-request), **LoRAX**, **ExpertWeave**, **InfiniLoRA** (2026, disaggregated),
  **Activated-LoRA** (cross-model KV-cache reuse, 2025). vLLM blog (Feb 2026) adds multi-LoRA for MoE bases.
- **MLX (our stack) — `mlx-optiq`:** **mounted LoRA hot-swap.** Wraps each target Linear in a `MountedLoRALinear`
  holding `{adapter_id: (A,B,scale)}` over the frozen base; a **`ContextVar` picks the active adapter per request**,
  so concurrent async requests with different adapters don't collide — **N adapters resident on one base, no reload.**
  `optiq serve --model <base> --adapter ./my_adapter`. **This IS our Level 3** — adopt it (MLX-first principle).
- **HF PEFT:** `add_adapter`/`set_adapter` (switch active), `hotswap_adapter` (in-place weight replace, avoids
  `torch.compile` recompile). **Constraint:** hot-swap needs **uniform rank / alpha / target-modules** across adapters.

## 4. Where we're AHEAD of the field
- **Eliteness, not just task-coverage.** Most MoErging libraries are task-LoRAs trained on benchmark datasets
  (FLAN/NIv2 tasks). Ours are **masters-grounded, audit-gated, verifier-backed** — a quality axis the papers lack.
- **The hybrid (generalist soul + specialist code)** the survey calls underexplored — we're already building it
  (Pattern B: fuse the soul into the base, then thin code adapters).
- **On-device / MLX** — the field is CUDA/cloud-centric; us + `mlx-optiq` = an on-device modular-LLM.
- **Verified decoding + the soul** — differentiators no MoErging system has.

## 5. Gotchas the literature flags (so we don't trip them)
1. **Standardize adapters** — same rank (we use 16), alpha, target-modules — or hot-swap recompiles/breaks.
2. **Token-level routing adds latency** — example/task-level (our case) is the cheap, right choice.
3. **Routing quality degrades as the library grows** → move to retrieval (CARLoS) past ~a dozen modules.
4. **Mis-routing happens** → always keep the **`<module>core</module>` fallback** (the soul handles anything unmatched).

## 6. The plan this implies
- **Serving (Level 3):** evaluate **`mlx-optiq`** for N-resident-adapter hot-swap on our base (replaces "reload the
  whole serve" — the only reason swaps were slow). Validate it loads our q3a4 base + our rank-16 adapters.
- **Routing (Level 2):** ship the **dispatcher gold** now; add **Arrow** training-free routing as the auto-fallback.
- **Library (Level 1):** keep adapters **uniform (rank 16, same targets)** so they're hot-swappable + composable.
- **Position the work** as a **verified, on-device, masters-curated MoErging system** — genuinely novel framing.

## 7. Round 2 — the June-2026 frontier (updates the plan)
- **Adapter GENERATION, not just selection:** Sakana **Text-to-LoRA (T2L)** + **Doc-to-LoRA (D2L)** (Feb 2026) —
  hypernetworks that emit a LoRA from a *text task-description* (T2L) or a *document* (D2L) in **one forward pass**
  (one-time meta-train → instant after). T2L matches task-specific adapters at ~4× less than in-context learning;
  D2L folds a 128K-token doc into a **<50 MB adapter** (vs ~12 GB KV-cache). **Factory endgame: *generate* a
  specialty on demand** instead of healing it. Caveat: matches *task*-LoRAs, not our masters-eliteness bar — a direction, not a drop-in.
- **Routing at scale:** **LORAUTER** (arXiv 2601.21795, Jan 2026) routes by **task representation** (task embeddings
  from a small validation set; *no adapter training data*) → scales with #tasks not #adapters; **oracle-matching
  (101.2%)** when an aligned adapter exists, **+5.2 on unseen**, robust to **1500+ noisy adapters**. Our scaling answer (supersedes CARLoS retrieval for us).
- **The MoE multi-LoRA "tax" — our base IS a MoE:** multi-LoRA on a MoE costs **4 LoRA-kernel ops per expert, per
  adapter** (gate_up + down, shrink + expand) — the bottleneck the vLLM/AWS Feb-2026 work targets. The "MoE Tax"
  analysis: swapping still saves **~95% VRAM**. **Measure this on our 77-expert base under `mlx-optiq`.**
- **Cross-base transfer → the demolition family ~free:** **LoRA-X** (2501.16559), **Cross-LoRA** (2508.05232),
  **Adapt-Once-Thrive-with-Updates** (2506.06844) transfer adapters across base versions **without retraining** →
  heal the soul *once* on the 106 GB base, **transfer to the 67/55/36/20/14 GB family (#53–58)** instead of re-healing each size.
- **More 2026 routing:** LoRA-Mixer (serial attention routing), DynMoLE (hybrid Tsallis-entropy), MoLoRA (per-token
  composable skills), Adaptive Minds (LoRAs-as-tools for agents).
- **The honest skeptic:** *"Position: Pause Recycling LoRAs"* (arXiv 2506.13479) — the field over-claims;
  recycled-adapter routing can underperform proper training. **Our guard:** only route when the scorecard shows it beats one soul'd model.
- **Apple frontier:** **Orion** (2603.06728) programs the Apple **Neural Engine (ANE)** for LLM inference — the on-device path beyond MLX-GPU.

**Net update:** near-term = `mlx-optiq` serving + **LORAUTER-style task routing** + uniform rank-16 adapters
(+ **cross-base transfer** for the family). Frontier = **T2L-style hypernetwork generation**. Discipline = the
skeptic's bar — route only if it *wins* on the scorecard.

## 8. Round 3 — production reality + the real-world proof
- **Apple Intelligence = this architecture, shipped to ~1B devices.** Apple's on-device foundation model is a
  **2-bit-QAT base (~3.7 bits/weight), frozen**, with **swappable per-task LoRA adapters** on all attention + FFN
  projections; the Swift **Foundation Models framework** adds **schema-constrained "guided generation"**
  (`@Generable` = our constrained decode), **tool-calling**, and KV-cache-aware sessions. **We independently built
  the same pattern — quantized base + swappable adapters + constrained decode + tools — on a 743B→99 GB *frontier*
  model instead of a 3 B.** The strongest possible validation. (Adapter specifics in the full report, arXiv 2507.13575.)
- **Composition (soul + code at once) → MERGE:** mergekit (8+ algos). **TIES** (trim → elect-sign → merge; scales to
  many), **DARE** (drop + rescale, a TIES pre-step), **Model/LoRA Soups** (linear avg). Rule of thumb: **3+ adapters →
  TIES, 5+ → DARE-TIES.** → Pattern B option 3: **TIES-merge soul + code** into one adapter (base stays pristine) instead of fusing the soul in.
- **LoRA on a quantized base (our q3a4) recovers the quant damage:** adapters give **<1% vs fp16 but +2–7% over the
  bare quantized base** — *the reason the soul heal works on 3-bit.* **LowRA** (arXiv 2502.08141) extends accurate LoRA
  **under 2 bits** → enables the 2-bit family (#57–58).
- **Production reality + the open lane:** **LoRAX** (Predibase — 100s of adapters/GPU, the open standard; → Rubrik
  Jun 2025) and **TGI Multi-LoRA** ("deploy once, serve 30") are production; Fireworks notably *lacks* LoRA serving.
  **No one ships a *curated, elite, verified* adapter library** — they're task-LoRA dumps. Our masters-trained, audit-gated library is the open lane.

[Round-3 sources: Apple AFM tech report 2025 + arXiv 2507.13575 · HF PEFT model-merging (TIES/DARE) · mergekit · LoRA Soups (2410.13025) · QLoRA · LowRA (2502.08141) · Predibase LoRAX · TGI Multi-LoRA (HF blog)]

## 9. Rounds 4–5 — the frontier hits our live decisions (June 2026)
- **MoE-LoRA placement (every future heal):** **MoE-Sieve** (2603.24044) — LoRA only the **top-25% most-routed
  experts** + attention/router/shared-expert → matches full LoRA at **70–73% fewer params**. Smaller, faster,
  more-uniform (∴ more hot-swappable) adapters. (Also TT-LoRA MoE; LoRA-on-the-router.)
- **The design degeneration = Computation Collapse (diagnosed):** "Signal Degradation vs Computation Collapse"
  (2604.19884) — our repetition + corrupted tokens (`UTF.FF9B`) on long-gen = **Computation Collapse** (early-layer
  component failure), **NOT** fixable by decoding tricks. Fix = **mixed-precision protecting salient/structurally-
  sensitive experts + early layers** (= our **#59** saliency-dynamic quant): SliM-LLM, **SFMP** (2602.01027, search-free),
  **Beyond-Outliers** dual numerical+structural sensitivity (2603.17354), channel-wise MP; MoE-specific Mixture-Compressor
  (2.54 bpw), ATOM. **Design is recoverable — keep salient design/early experts at 4-bit+.**
- **Curated-SFT validated:** **LIMA** (quality+diversity ≫ size; alignment *unlocks* pretrained ability) = our 250-gold
  soul; **"SFT on Curated Data is RL"** (2507.12856) → curated-SFT is implicit RL; **iw-SFT** (importance-weighted) a free upgrade to try.
- **REAP (our prune) = ICLR 2026 + a fix to adopt:** March-2026 update **renormalizes top-k router logits to sum to 1**
  (pull into our prune); paper **confirms prune > merge for generative** (vindicates #19); **router calibration after
  prune** matters (2603.02217) — verify ours.
- **Self-reward hacks → verifiable reward wins:** Self-Rewarding / Meta-Rewarding (2401.10020) — self-training real
  problems **reward-hacks**; needs **verifiable rewards** = our verifier mesh / RLVR (why GRPO→SFT). The field validated our instinct.
- **Constrained-decode quality tax is fixable:** **XGrammar-2** (May 2026; default for vLLM/SGLang/TensorRT, <40µs/tok,
  bitmask) — the 10–30% quality drop is an **enforcement artifact**, removable. Align our **#32** MLX constrained-decoder;
  verify it isn't taxing quality. (Pre3 2506.03887; Draft-Conditioned 2603.03305.)
- **Newest routing:** Brainstacks (2604.01152 — 7-projection routing + adapter *stacking* + disk-offload), MoA
  (heterogeneous experts), LoRA-Mixer (attention-routed), Reversible Lifelong Editing (2603.11239).

[Rounds 4–5 sources: MoE-Sieve 2603.24044 · Computation-Collapse 2604.19884 · SFMP 2602.01027 · Beyond-Outliers 2603.17354 · SliM-LLM · LIMA · SFT-is-RL 2507.12856 · REAP 2510.13999 (ICLR'26) · Router-Calibration 2603.02217 · Self-Rewarding 2401.10020 · XGrammar-2 2411.15100 · Brainstacks 2604.01152 · LoRA-Mixer 2507.00029]

## 10. Round 6 — "how others do it" + our architecture (validates #69, the DSA, the serve)
- **HF/MLX community:** mlx-community **~4,810 converted models**; MoE kernels mature (late-2025); 3–8 bit +
  mixed-precision (**mxfp8/nvfp4** — for #59). Qwen3-Coder-30B-**A3B** MoE ~130 tok/s on M4 Pro (vs 43 Ollama) — but
  3B-active; **our 11–14 tok/s is the active-param count, not MLX** (confirms SPEED.md). Also Rapid-MLX, vLLM Apple ports, M5-GPU neural accelerators.
- **DSA = DeepSeek Sparse Attention (our architecture):** ~98% attention-compute cut at 128K via **fixed top-2048
  tokens/query** = our `index_topk: 2048` = the heal max-seq-2048 limit (the scatter-VJP). **DeepSeek-V4** (Apr 2026):
  hybrid compression+sparse, 27% FLOPs / 10% KV-cache of V3.2 at 1M ctx — the architecture's future.
- **Spec-decode dead on big MoE (#69) — confirmed:** EAGLE-3.1 (May 2026) great on DENSE; literature explicit that
  **large-MoE break-even rises until spec-decode HURTS**, MoE drafts "largely unexplored." Our exact finding.
  **SpecForge** (2603.18567) = the open training framework IF we build the fresh EAGLE head.
- **KV-cache quant for the serve (the 118 GB crash):** **TurboQuant** (Google ICLR'26 — 6× KV, 8× attn, no calib),
  **KVQuant** (sub-4-bit, 10M ctx), KIVI, Cocktail — headroom for long runs.

[Round-6 sources: mlx-community (HF) · MLX-on-M5 (Apple ML) · DeepSeek-V3.2/V4 (2512.02556, vLLM 2026-04-24) · Native Sparse Attention 2502.11089 · EAGLE-3.1 (MarkTechPost 2026-05) · SpecForge 2603.18567 · TurboQuant (Google ICLR'26) · KVQuant · KV-cache survey (MarkTechPost 2026-04)]

## 11. Round 7 — adjacent pillars (validates #8 KD, #33 kernels, contamination-checking)
- **On-policy distillation (#8) = industry default:** student samples own trajectories + teacher dense
  token-supervision (fixes off-policy mismatch). **Qwen3, DeepSeek-V4, Gemma 2, MiMo-V2 all adopt OPD** — we were
  early. Extensions: **Lean-OPD** (self-teacher critiques the student's Lean attempt → our prover #27-31),
  **Self-Distilled Reasoner** (2601.18734, on-policy self-distill). Survey 2604.00626; Thinking Machines OPD.
- **Contamination-checking vindicated:** a 2026 dose-response study (Qwen3 34M-344M, sweep test-replicas) resolved
  the 2024-25 split → contamination **does** inflate, measurably. Our 0/0/0.4% near-dup check = right discipline.
  Honest set = contamination-resistant **LiveCodeBench / LiveBench / MMLU-Pro / FrontierMath** (= our #66).
  Detection: Min-K%, ConStat, canary-GUID, time-partition.
- **M5 + MLX kernels (#33):** M5 (Mar 2026) = Neural Accelerators in each of 40 GPU cores → **up to 4× TTFT**
  (matrix-mul in silicon); MLX exploits via kernel **fusion** (Metal 4 + TensorOps), llama.cpp doesn't = our #33
  approach. Speeds **prompt-processing**, not bandwidth-bound decode (our 11-14 tok/s floor holds). (Aside: native-MTP
  spec-decode now works on a 27B/MLX — but that's small/dense; our 743B-MoE #69 finding stands.)
- **Agent memory (#57 compaction):** 2026 frontier = autonomous compaction (MIRIX, A-Mem: compress/prune) +
  **provenance-verified tiered memory** (2602.17913 — integrity-aware, like our agent). **AMA-Bench** (2602.22769) to measure.

[Round-7 sources: OPD survey 2604.00626 · Self-Distilled Reasoner 2601.18734 · Lean-OPD · Contamination dose-response 2026 · contamination-resistant benchmarks · M5 MLX Neural Accelerators (Apple) · Provenance-Aware Tiered Memory 2602.17913 · AMA-Bench 2602.22769 · ACON 2510.00615]

## 12. Round 8 — agentic pillars + a live-bug fix (overthinking)
- **Overthinking (fixes GSM8K + a speed win):** 2025-26 result — **longer CoT ≠ better**; o1-style models overthink
  easy problems → degrade accuracy + miscalibrate. Our 5–8K-token CoT = textbook overthinking = what broke the GSM8K
  parser (no clean final answer). **Shorter chains = better accuracy + fewer tokens at 11-14 tok/s.** Tune `enable_thinking`
  shorter. ("Don't Overthink It" 2505.17813; "When More Thinking Hurts" 2604.10739; deep-thinking-token quality 2602.13517).
- **Competitive (validates base, flags benchmark trap):** GLM-5.x among open models that **closed the gap** on closed
  frontier for multi-step coding (w/ DeepSeek-V4, Kimi-K2.6, Qwen-3.6). But **SWE-bench is saturating** — OpenAI stopped
  reporting it ("scoring" vs "useful" diverged). Weight real-task benches: FeatureBench (2602.10975), Terminal-Bench, LongCLI-Bench (2602.14337) for #62.
- **Agent security (our 5-layer matches SOTA):** prompt-injection = OWASP LLM01 (3yr running). Live threats: **RAG
  poisoning (5 docs → 90%)**, **tool poisoning** → LlamaFirewall (2505.03574), CausalArmor (2602.07918), TRUSTDESC
  (2604.07536). **Zombie Agents** (2602.15654 — self-evolving-agent injection) = a flywheel risk to guard.
- **Agentic RAG (CallSieve upgrade):** retrieval-as-agent-tools (A-RAG 2602.03442: hierarchical keyword+semantic+chunk-read),
  iterative multi-hop, multi-agent retrieve+validate+synthesize. SoK 2603.07379. Upgrade path for our CallSieve/live-docs.

[Round-8 sources: Overthinking 2604.10739 / 2505.17813 / 2602.13517 · SWE-bench-Verified leaderboard · FeatureBench 2602.10975 · LongCLI-Bench 2602.14337 · OWASP LLM01 · LlamaFirewall 2505.03574 · CausalArmor 2602.07918 · TRUSTDESC 2604.07536 · Zombie-Agents 2602.15654 · A-RAG 2602.03442 · SoK Agentic-RAG 2603.07379]

## 13. Round 9 — saturation (the floor; mostly confirms)
- **Extreme low-bit (family #57-58):** BitNet b1.58 (ternary {-1,0,1}, ~90% mem, 38.8× energy on 30B), BitNet-v2
  (4-bit activations), Sparse-BitNet (1.58-bit + N:M), PTQ1.61. **Caveat: BitNet needs QAT/training — our PTQ at 2-bit
  is lossier; the 2-bit family stays the flagged experiment.**
- **GGUF/llama.cpp (#51):** K-quants (Q2_K–Q6_K), i-quants + importance matrices, MoE CPU+GPU split (active→GPU, experts→CPU). The non-MLX path.
- **On-device multimodal:** Apple AFM (confirmed); **FastVLM** (FastViTHD, 85× faster TTFT) = Apple's edge VLM encoder (ref for vision #43); unified shared-backbone multimodal.
- **VERDICT: research saturated.** Rounds 5–9 increasingly *confirmed* our builds (prune>merge, verifier-mesh, OPD,
  MLX-fusion, DSA top-2048, contamination-checking) rather than revealing new levers. Net-new actionables have
  stabilized → see `IMPLEMENTATION_PLAN.md`.

[Round-9 sources: BitNet b1.58 / v2 2504.18415 · Sparse-BitNet 2603.05168 · PTQ1.61 2502.13179 · llama.cpp quant eval 2601.14277 · FastVLM · Apple AFM 2507.13575]

## Sources
- [A Survey on Model MoErging (arXiv 2408.07057)](https://arxiv.org/pdf/2408.07057)
- [Towards Modular LLMs by Building and Reusing a Library of LoRAs (Ostapenko)](https://www.semanticscholar.org/paper/6839e8ef0205ad4732e9f743977eb5bfc296ec2c)
- [Learning to Route Among Specialized Experts for Zero-Shot Generalization — PHATGOOSE (arXiv 2402.05859)](https://arxiv.org/pdf/2402.05859)
- [LD-MoLE: Learnable Dynamic Routing for Mixture of LoRA Experts (arXiv 2509.25684)](https://arxiv.org/abs/2509.25684)
- [X-LoRA: Mixture of low-rank adapter experts (APL Machine Learning)](https://pubs.aip.org/aip/aml/article/2/2/026119/3294581/)
- [Glider: Global and Local Instruction-Driven Expert Router (EMNLP 2025)](https://aclanthology.org/2025.emnlp-main.319.pdf)
- [CARLoS: Retrieval via Concise Assessment Representation of LoRAs at Scale (arXiv 2512.08826)](https://arxiv.org/html/2512.08826)
- [S-LoRA: Serving Thousands of Concurrent LoRA Adapters (arXiv 2311.03285)](https://arxiv.org/pdf/2311.03285)
- [vLLM multi-LoRA serving (Feb 2026)](https://vllm.ai/blog/2026-02-26-multi-lora)
- [InfiniLoRA: Disaggregated Multi-LoRA Serving (arXiv 2604.07173)](https://arxiv.org/pdf/2604.07173)
- [mlx-optiq — mounted-LoRA hot-swap on Apple Silicon (PyPI)](https://pypi.org/project/mlx-optiq/)
- [HF PEFT — Hotswapping adapters](https://huggingface.co/docs/peft/v0.14.0/en/package_reference/hotswap)
- [Unsloth — LoRA hot-swapping guide](https://unsloth.ai/docs/basics/inference-and-deployment/vllm-guide/lora-hot-swapping-guide)
