# Design-Soul — elite, bespoke, heritage-grounded design out of the box

This model is tuned to design like it studied at the Bauhaus — not the cookie-cutter average of the web.
Here's why it needs help and how to get elite output.

## Why a frontier model is "competent, not elite" by default
1. **It learned the average.** Millions of hex-color / arbitrary-spacing / Bootstrap pages, few elite ones → its
   default reverts to the mean (competent).
2. **Knowing ≠ doing.** It can *describe* OKLCH, Rams, the Swiss grid (declarative) but doesn't *reach for* them
   unprompted (procedural).
3. **No pretraining reward** ever said "elite > average." So it has no preference.

The fix is **activation** — pushing the model onto its latent elite-art manifold. Six rungs, shallow→deep:

| Rung | Mechanism | In this repo |
|---|---|---|
| 0 Prompt naming | "Swiss style" nudges attention | `CANON` (below) |
| 1 Dense priming | flood the context with names/era/type | `CANON` HERITAGE block |
| 2 Few-shot | show a gold exemplar in-context | `seeds/*.html` |
| 3 Persona | "you are Müller-Brockmann, 1958" | prompt |
| 4 **Activation steering** | inject the elite *direction* into the residual stream (ActAdd/RepE) | `design_steering.py` |
| 5 Heal (permanent) | SFT on gold → bake the direction into weights | `design_flywheel.py` |

The **gold seeds define "elite" at every rung** — the few-shot exemplar, the steering vector
(`mean(elite acts) − mean(cookie-cutter acts)`), and the heal target. One contrast set, every depth.

## Use it today (rungs 0–2)
Prepend **`CANON`** as your system prompt, then **invoke a tradition**:
> *"A pricing page in the Swiss International style."*  ·  *"A Rams-minimal settings panel."*  ·  *"A De Stijl dashboard."*

`audit_design(html)` gates the output: **OKLCH-only · 8px grid · 1.25 type scale · bespoke (rejects
Bootstrap/Tailwind-soup/MUI/React)**. `is_elite(html)` → bool.

## The CANON (copy this as your system prompt)
```
You are an ELITE product designer. Every design obeys these non-negotiables — they separate competent from elite:

HERITAGE — you know hundreds of years of design; CHANNEL it, never design generically:
  • Swiss / International Typographic Style (Müller-Brockmann, Hofmann) — the grid as structure, asymmetric balance, sans-serif clarity, generous negative space
  • Dieter Rams — "as little design as possible"; honest, unobtrusive, long-lasting
  • Albers & Itten — interaction of color, simultaneous contrast (OKLCH is your modern tool for exactly this)
  • Bauhaus — form follows function; geometric clarity; the union of art and craft
  • Editorial rigor (Vignelli, Tschichold, Pentagram) — typographic hierarchy, the modular scale, restraint
  Design IN a tradition; when the user names one ("Swiss", "Rams-minimal", "editorial", "brutalist", "Memphis"), commit to it fully — its palette, its grid, its type, its ethos.

COLOR — oklch() ONLY. Never hex, rgb(), or hsl().
  • one brand hue; derive shades by varying L at fixed C/H, as CSS custom properties
  • neutrals are oklch with C≈0.01-0.03 (never pure gray — carry a hint of the brand hue)
  • WCAG AA: body text ≥ 4.5:1, large/UI ≥ 3:1 vs its background
SPACING — 8px GRID. Every margin/padding/gap is a multiple of 4 (4 8 12 16 24 32 48 64). No 5px/13px/23px. Borders may be 1px.
TYPE — modular scale, ratio 1.25: 12 16 20 25 31 39 49px. Line-height 1.5 body, 1.2-1.3 headings. ≤2 families.
LAYOUT — hierarchy via SIZE+WEIGHT+SPACE (not color alone); generous whitespace; consistent radius; subtle single-direction shadow; align to the grid.
RESTRAINT — 1 brand hue + neutrals + ≤1 accent; ≤2 fonts; few shadows. Elite design is what you remove.
BESPOKE — hand-write the CSS. NO Bootstrap, NO Tailwind utility-soup, NO Material-UI/Chakra/Ant, NO framework component classes. Semantic class names, custom properties, grid/flexbox from scratch. Cookie-cutter is the enemy — every layout is its own.

Output production-ready HTML+CSS with CSS custom properties for the OKLCH palette and the spacing scale.
```

## Gold seeds (`seeds/`) — 9 hand-authored, all `audit_design`-verified (0 violations)
`swiss` · `rams` · `bauhaus` · `destijl` · `editorial` (named movements) + `pricing` · `hero` · `dashboard` · `login`.
These are *above* the model's current ceiling on purpose — that's what raises it.

## Files
- `design_canon.py` — `CANON` + `audit_design()` / `is_elite()` / `cookie_cutter_tells()`
- `design_steering.py` — `steering_vector()` + `apply_steering(model, layer, v)` (rung 4, ActAdd/RepE)
- `design_flywheel.py` — generate → audit → self-correct → keep-elite → SFT corpus (rung 5)
- `seeds/` — the nine gold designs + `seeds.jsonl` (the heal corpus)

## Beyond design — the recipe generalizes to every facet (`soul.py`)
Each hat has masters whose knowledge is latent in the weights; the *same* move (name the lineage → gate →
steer → heal) makes the model elite anywhere. `soul.py` carries a heritage canon + gate per facet, with a gold
seed each in `facets/seeds/`:

| Facet | Heritage | Gate |
|---|---|---|
| 📊 dataviz | **Tufte** · Cleveland · grammar of graphics | chartjunk / data-ink |
| 💻 code | Kernighan & Pike · Unix · Knuth | live verifier (compile+lint) |
| 🔒 security | **Saltzer & Schroeder** · OWASP · Kerckhoffs | secrets + insecure-primitives |
| ✓ math | Erdős's "The Book" · Pólya | live verifier (Lean) |
| ✍️ prose | Strunk & White · Zinsser · Orwell | AI-slop |
| 🏛 architecture | **Alexander** (A Pattern Language) · Parnas · the dependency rule | review |
| 🔬 research | **Feynman** · the scientific method · Popper · citation discipline | groundedness (claims cited + verified in-source) |

`design_steering.py` + `design_flywheel.py` are facet-agnostic — they take any `FACETS[name].audit` as the
elite/generic contrast. One steering module, one flywheel, every facet.

## The Demolition family — shrink but keep the soul
The elite training lives in the heal corpus + the facet-inclusive calibration (`78_facet_calib.py`), both
**size-agnostic** — so every size stays elite. The soul-retention experiment (`79_demolition_family.py` builds,
`80_family_eval.py` scores each via the soul gates):

```
 ~106GB : ████████  77 experts · 3-bit  (baseline, this model)   → 128 GB Mac
   67GB : ██████    46 experts · 3-bit                           → 96 GB Mac
   55GB : █████     36 experts · 3-bit                           → 64 GB Mac
   36GB : ███       26 experts · 2.5-bit                         → 48 GB Mac
   20GB : ██        16 experts · 2-bit  ⚗️                        → 32 GB Mac
   14GB : █          8 experts · 2-bit  ⚗️ (floor; ~10.4GB base)  → 24 GB Mac
  (sizes MEASURED: ~10.4GB fixed base + experts × ~1.24GB × bits/3; <~13GB impossible)
```

Per size: facet-calib → saliency → prune harder → quantize → heal (the soul corpus) → scorecard (% elite per
facet). Same masters-trained soul, every Mac.
