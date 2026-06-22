# The Design Soul — the canon (and an honest status)

> **Status (2026-06-22):** the philosophy + canon below are *real and reusable* — this is the elite design
> training data. But **measured** on the *demolished* v3 base, the design-soul adapter was neutral-to-degrading
> (see `MISSION_SUMMARY.md` — soul heals don't lift the demolished model). So treat this as the **gold for a
> soul on a *clean* base** (Qwen3-Coder-30B), not a proven win on v3. The original "beats Fable" framing was
> aspirational; the canon is what's true and carries forward.

## The thesis (one grammar)
Beauty is **mathematics made visible and feeling made structural.** The same grammar
recurs across scales and domains: the golden angle packs a sunflower *and* spirals a
galaxy; the logarithmic spiral is a nautilus, a hurricane, a galaxy's arm; Voronoi is
a dragonfly wing *and* the cosmic web; Gaudí grew columns from trees; van Gogh painted
turbulent flow before physics could model it. **A scrolled, navigated web app is
architecture in space and time.** Most of the web looks cookie-cutter because it's made
with a graphic-design eye but no architectural, natural, or philosophical one. We give
the model *all* of it, as one internalized grammar — so it designs from the **source of
beauty**, not from a framework default.

## The canon we build into the model
| Module | Covers | Script |
|---|---|---|
| Art canon | fine art 1450→2026, color theory, OKLCH, AesCode, anti-framework | `design_curriculum/history/patterns`, `aescode` |
| Creative-coding | the "be the world *inside* the painting" genre; generative/immersive | `31` + `design_out/exemplars/` |
| Architecture | proportion, procession, scale, light, materiality, structure, void, threshold; pyramids→Chicago frame→NYC Deco→Burj Khalifa→the great houses | `35` |
| Nature · math · cosmos | golden angle/φ, log spirals, fractals, Voronoi, L-systems, boids, reaction-diffusion, waves, symmetry; orbits, galaxies, scale, starlight | `36` |
| Design soul (connective) | typography, perceptual color, motion-as-physics, Gestalt, human perception, musical rhythm, narrative, materiality/light, **the philosophy of taste** (wabi-sabi, Ma, Dieter Rams) | `37` |

## How the capability lives in the MODEL (not in Claude)
1. **Training data** — each module emits `heal/mine/*.jsonl` (principle → web translation
   → concrete modern-vanilla technique). Folded into the heal so the *weights* carry it.
2. **Master system prompt** — `design_out/design_soul_system.txt`, the distilled taste,
   used as the design system prompt at serve time.
3. **Render-critique verifier** (`25`) — measures the output (contrast, type scale, OKLCH,
   proportion, rhythm, framework-tells); the objective signal.
4. **Best-of-N self-play** (`26 --mode design`) over the curriculum briefs
   (`design_out/briefs_*.json`) — generate N, render+measure, keep the best as *new*
   training data → next heal. This is how taste scales without hand-authoring every scene.
5. **Gold exemplars** (`design_out/exemplars/`) — a few hand-authored targets (e.g. the
   Starry Night *world*) that set the bar; the model learns toward them, then surpasses
   via self-play. (Authoring gold data is capability-building, not "Claude doing it.")

## How this beats Fable on design (in our niche)
Fable emits one strong, broadly-trained shot. We emit a **bespoke design generated from
first principles of beauty**, then **measure it and iterate** (best-of-N on the critic) —
and we can prove it with `29_design_vs_fable` (fewer measured findings = win). Frontier
breadth vs. our **specialized grammar + verification loop + self-play flywheel**. Same
formula as the code side: *we don't out-know it, we out-verify it.*

## The standard
Bespoke over template. Proportion over arbitrary. Void as material. Motion as physics.
Color as light. One crafted hand-made detail. **Would it still feel right in ten years?**
Remove until only the inevitable remains — then stop.
