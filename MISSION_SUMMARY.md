# Mission Summary — the honest verdict (2026-06-22)

After many measured autonomous ticks chasing speed + accuracy on the demolished GLM-5.2, here is the
straight, evidence-based conclusion. **Numbers measured, not hoped.**

## The core finding: the demolished 4-bit base is at its ceiling
Every lever to make it *meaningfully better* was tried and measured:

| Lever | Result (measured) |
|---|---|
| **#113 fix-packet++** (spotlight the failing assertion) | ✅ **helps simple bugs** — resolved a clamp `return x→hi` flip candidate-1 |
| **#118 Reflexion** (verifier-feedback retry) | 🔧 built, sound — but **didn't fix harder bugs** (base can't reason the fix) |
| **#114 base re-heal** (flywheel gold) | ❌ flywheel produces **100% MBPP Python flips** — wrong gold, +17 unique, marginal |
| **Soul heals** (security, rank16/iters200) | ❌ **DEGRADED** security (base named parameterized queries; soul went generic) |
| **Soul heals** (security, gentle rank8/iters60) | ⚪ **neutral** — ≈ base, no degrade *and no lift* |
| **Spec-decode** (EAGLE/MTP/DFlash) | ❌ ~**1.05×** on M5 for a 98 GB model (bandwidth wall; CUDA's 8× doesn't translate) |
| **Clean base vs demolished** | ❌ a clean Qwen-7B beat the demolished 744B on **speed AND quality** |

The model also **degenerates into noise** on some prompts (e.g. "secure password hash") regardless of adapter
— a fundamental 4-bit limitation, not fixable by heals.

## What actually works (the real deliverables)
1. **merle** — the public, MIT, model-agnostic, verify-first coding CLI. The harness is genuinely good
   (streaming, loop-proof, fix-packet++, callsieve embedded). *This is the product.*
2. **The working v3 base** — **HumanEval-164 pass@1 = 114/164 (69%)** (full set, single-shot, real-verifier-
   scored; the easy n=20 subset was 95%). 69% single-shot is *mid-tier and genuinely usable* for a demolished
   4-bit model on a laptop (≈ GPT-4-class on this metric; below dedicated frontier coders ~90%) — and the
   verify-loop (best-of-N) lifts it further. Solid at writing vanilla FOCUS-9 functions from a spec; weaker on
   harder debugging/multi-step + off-distribution. The "at ceiling" finding is about *improving* it (heals
   don't); its *level* is decent. Private on HF (`q4a4-soul`).
3. **The multimodal stack** — 7/7 light lanes (embed/rerank/NER/tabular/RAG/web/TTS) **verified producing
   real output**, not just wired.
4. **The honest research map** — the dead-lever table above is itself a result: it tells anyone building a
   local model on Apple Silicon what *not* to waste weeks on.

## The honest recommendation
Stop trying to make the demolished giant elite — it can't be, at any bit-width (3-bit broke, 4-bit works-but-
limited, 2-bit worse). The **methods** (REAP, the heal recipe, the flywheel, the verifiers, the souls) are the
transferable value; the right *vehicle* is a **clean right-sized model** (Qwen3-Coder ~30B), which merle already
supports via `MERLE_BASE`. The demolition is a legitimate **research artifact** — "744B → laptop" — now **public**
(https://huggingface.co/philipjohnbasile/GLM-5.2-Demolition-q4a4-soul-MLX, MIT), published as an honest
*best-possible-demolition* study, not a daily driver.

**Discipline held throughout:** every claim measured, every dead lever dropped honestly, nothing faked.
