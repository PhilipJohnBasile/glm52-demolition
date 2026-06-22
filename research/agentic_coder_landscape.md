# THE Local Agentic Coder — landscape + our path (June 2026)

Goal: make this model **THE** model for *local agentic coders*. This is the competitive scan + the honest
strategy that falls out of it.

## The field (local/open agentic coders, June 2026)
| Model | Agentic headline | License |
|---|---|---|
| **Qwen3-Coder-Next** | 58.7% SWE-bench-Verified, 256K ctx, **runs on 24 GB** — purpose-built for agentic loops; *the* local bar | open |
| **DeepSeek-V4** (Pro 1.6T/49B · Flash 284B/13B) | 1M ctx, long-horizon planning, **improved tool-call reliability** (fewer malformed JSON) | MIT |
| **GLM-5.1** (our base's sibling, 754B) | **58.4 SWE-Pro, 8-hour autonomous execution** — SOTA agentic | MIT |
| **Kimi K2.6 Thinking** | 78.57 coding / 58.33 agentic — strongest open | Modified-MIT |
| **Qwen 3.6 Plus** | 1M ctx, reliable tool-use over long sessions | open |
| frontier ref: **Claude Opus 4.6** | 50% task completion @ **14.5-hour** horizon | closed |

**They compete on:** context length · raw SWE-bench · **tool-call reliability** · long-horizon autonomy · speed.

## Where we honestly *can't* win
Raw size (we demolished GLM-5.2 → 99 GB / 3-bit), decode speed (11–14 tok/s), context (vs 1M), raw SWE-bench
(70 % of experts pruned). Chasing those is a losing race against un-demolished 24 GB models.

## Where we WIN — agentic *reliability* (the thing that actually breaks agents)
The research names **tool-call reliability as the #1 agentic differentiator** (DeepSeek-V4's headline win was
*"fewer malformed JSON / partial calls"*). We don't improve it — we **guarantee** it:
- **Constrained tool-JSON (#45):** grammar-enforced tool-calls → **zero** malformed JSON, structurally impossible. (Field's best = "fewer"; ours = "none.")
- **Compiler-steered / verified decoding (#21, #24):** every line type-checks *as it's written* (TS 0.3 ms · Py ~0 · Rust 34 ms).
- **Fabrication-proof `done` (#41):** re-runs the *original* tests → can't hallucinate a pass.
- **Integrity layer:** test-tamper guard, secret-scan (16 providers), scope enforcement, slopsquat guard.
- **51-tool ReAct agent:** trajectory compaction, stall detection, the verifier mesh (5 langs + SQL + Lean).

**Positioning:** *"the local agentic coder that can't malform a tool-call, can't fake a test pass, and
compiler-checks every line."* The others are bigger/faster; **none** ship the verify-everything stack. Reliability
is a moat raw capability can't buy — and it's exactly what makes long agentic runs not collapse.

## Adoptable from the field (CPU now → heal later)
1. **Tool-use cold-start SFT** (AgentRL / ProRL pattern): query-formulation → tool-invocation → valid-JSON →
   result-read → recover-from-error. → generate **agentic tool-use gold** for the next soul heal.
2. **Long-horizon agentic data** (128 turns / 131K ctx, Hierarchy-of-Groups PO): multi-step plan→edit→test→fix
   trajectories that *don't* lose the thread. Our agent is built for it — train + benchmark it.
3. **Tool-call self-correction** (DeepSeek-V4's win): recover from a bad call. (Our constrained decoder prevents
   the bad call upstream — but the *recovery* skill still helps when external tools fail.)
4. **Atomic skills** ("Scaling Coding Agents via Atomic Skills", 2604.05013): decompose tasks into reusable skills → our skill library.
5. **MCP / OpenAI-compat integration:** the field plugs local models into Cline · OpenCode · Aider · Claude Code via
   OpenAI-compat + MCP. We already serve OpenAI-compat (`mlx_lm.server`) — document the one-line setup per agent so we're a drop-in.

## Plan
- **NOW (CPU):** (a) position the card around **agentic reliability**; (b) generate agentic tool-use + long-horizon +
  reliability gold (`heal/gold_agentic/`) for the next heal; (c) document the Cline/OpenCode/Aider/Claude-Code drop-in setup.
- **LATER (GPU, behind the factory + #59):** heal the agentic gold into the soul; benchmark long-horizon
  (Terminal-Bench / FeatureBench / real-task, *not* the saturating SWE-bench); the #59 collapse fix keeps long agentic gens from degenerating.

*Sources: Qwen3-Coder-Next / DeepSeek-V4 / GLM-5.1 (MarkTechPost, kilo.ai, mindstudio 2026) · Agentic Tool Use 2604.00835 · AgentRL/ProRL 2603.18815 · Hierarchy-of-Groups PO 2602.22817 · Atomic Skills 2604.05013 · CWM 2510.02387 · OpenCode/Cline (morphllm 2026).*
