#!/usr/bin/env python3
"""The design soul — the connective curriculum that completes the canon (art 31,
architecture 35, nature/cosmos 36): typography, perceptual color, motion-as-
physics, Gestalt composition, human perception, musical rhythm, narrative,
materiality/light, and the PHILOSOPHY of taste (wabi-sabi, Ma, Dieter Rams). Each
as principle -> web translation -> concrete modern-vanilla technique. Also emits
the MASTER design-soul system prompt the serve stack should use.

  python scripts/37_design_soul.py
-> heal/mine/design_soul.jsonl  (+ design_out/design_soul_system.txt, briefs_soul.json)
"""
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")

MASTER = (
    "You are a master designer-engineer carrying the internalized taste of the whole "
    "canon: fine art (1450 to 2026), architecture (the pyramids to parametric), the "
    "mathematics of nature and the cosmos, typography, perceptual color, motion as "
    "physics, Gestalt composition, human perception, musical rhythm, narrative, "
    "materiality and light, and the philosophy of beauty (wabi-sabi's perfect "
    "imperfection, Ma's active emptiness, Dieter Rams's 'less but better'). You design "
    "web experiences as architecture in space and time, GENERATED from the grammar of "
    "beauty: proportion from the golden ratio, motion from real fields (flow, springs, "
    "orbits), color from light, structure from honest grids, growth from fractals and "
    "phyllotaxis. You write modern hand-crafted vanilla JS/CSS — Canvas/WebGL/SVG, "
    "OKLCH, scroll-driven animation, View Transitions, :has(), subgrid, container "
    "queries, variable fonts — no framework, no library. Every result is bespoke, "
    "contextual, accessible, and timeless. Never cookie-cutter, never a default theme.")

# (domain, principle + canon, web translation, concrete technique)
SOUL = [
    ("Typography — the craft",
     "From Jenson and Garamond to Bodoni's contrast to Swiss/International (Müller-"
     "Brockmann) to Bringhurst's Elements: a measure of 45-75 characters, leading "
     "that loosens as size drops, a modular scale, and a clear hierarchy are most of "
     "what makes a page read as designed.",
     "a proportional type scale, an ideal measure, optical fluid sizing, and tracking "
     "tightened only for display",
     ":root{--step-0:clamp(1rem,.9rem+.4vw,1.15rem);--step-2:clamp(1.6rem,1.2rem+2vw,"
     "2.6rem)} p{max-width:66ch;line-height:1.55} h1{letter-spacing:-.02em;"
     "line-height:1.05;font-variation-settings:'opsz'72}"),
    ("Perceptual color",
     "Color is light, not swatches. OKLCH is perceptually uniform, so harmonies (hue "
     "angles), gradients, and dark mode behave; interpolating in sRGB dies through a "
     "grey zone, OKLCH stays luminous. Accent with restraint (60/30/10).",
     "an OKLCH token system; harmonies by rotating hue; gradients and states computed "
     "in OKLCH; dark mode by lowering lightness and chroma, not inverting",
     "--accent:oklch(0.62 0.19 145);--accent-2:oklch(0.62 0.19 285); /* complementary "
     "= +180° hue */ .grad{background:linear-gradient(in oklch,var(--accent),"
     "var(--accent-2))}"),
    ("Motion as physics",
     "Disney's 12 principles (anticipation, follow-through, staging, ease) and spring "
     "dynamics make motion feel alive. Real interfaces move like mass on a spring, not "
     "linear. Choreograph with stagger; animate only compositor props.",
     "spring/eased motion, staggered reveals, micro-interaction feedback, scroll-"
     "driven choreography — transform/opacity only, and honor reduced-motion",
     "@media(prefers-reduced-motion:no-preference){.item{animation:rise .6s "
     "cubic-bezier(.2,.8,.2,1) both;animation-delay:calc(var(--i)*60ms)}}"),
    ("Gestalt & composition",
     "The eye groups by proximity, similarity, closure, continuity, common fate, and "
     "figure-ground. One focal point; a reading path (Z or F); tension and balance on "
     "a Swiss grid; the rule of thirds and dynamic symmetry.",
     "spacing that groups meaning, a single clear focal point per view, an honest grid, "
     "asymmetric balance with intentional tension",
     ".group{display:grid;gap:.25rem} .group + .group{margin-top:2rem} /* proximity = "
     "meaning */ main{display:grid;grid-template-columns:1.618fr 1fr}"),
    ("Human perception & cognition",
     "Preattentive attributes (color/size/orientation 'pop' pre-thought); Fitts's law "
     "(big, near targets); Hick's law (fewer choices, faster); Miller's 7±2 (chunk); "
     "the aesthetic-usability and peak-end effects; Von Restorff (isolate to "
     "emphasize).",
     "make the one important thing preattentively pop, size primary targets generously, "
     "chunk choices, design the peak and the ending, isolate the key action",
     ".cta{min-block-size:3rem;padding-inline:1.5rem} /* Fitts */ .badge{filter:"
     "saturate(1.4)} /* preattentive pop / Von Restorff isolation */"),
    ("Musical rhythm",
     "Design has tempo. Spacing is meter; repetition with variation is theme-and-"
     "variations; the hero is the crescendo/drop. Timing in small-integer ratios "
     "(1:2:3) feels composed — the music of the spheres in the UI.",
     "a spacing scale as a rhythmic meter, paced reveals, a built crescendo, animation "
     "durations in harmonic ratios",
     "--beat:0.5rem; /* meter */ .stack>*+*{margin-top:calc(var(--beat)*3)} "
     ".fast{transition-duration:200ms} .slow{transition-duration:400ms} /* 1:2 */"),
    ("Narrative & emotion",
     "A scrolled page is a story arc: setup, tension, climax, resolution. The reveal, "
     "the pause, the turn. The hero's journey shapes onboarding and landing; pacing "
     "creates feeling.",
     "structure the scroll as acts, stage a reveal and a climactic moment, use pauses "
     "(whitespace) as beats, resolve",
     "/* sections as acts: hook -> build (proof) -> climax (the offer) -> resolution "
     "(close). Pace with view-timeline reveals and generous interstitial void. */"),
    ("Materiality & light",
     "The cinematographer's eye: a consistent key light, fill and rim; depth of field; "
     "color grading; the golden hour. Choose flat, glass, or tactile honestly; grain "
     "and one light source give believable depth.",
     "an elevation system from one light source, restrained glass, subtle grain, a "
     "graded palette and atmospheric depth",
     "body{background:radial-gradient(120% 80% at 50% -10%,oklch(.3 .04 260),"
     "oklch(.16 .03 260))} .card{box-shadow:0 1px 2px oklch(0 0 0/.3),0 12px 32px "
     "oklch(0 0 0/.22)} /* one light, ranked depth */"),
    ("The philosophy of taste",
     "Judgment, not just knowledge. Wabi-sabi: perfect imperfection, transience, the "
     "hand-made. Ma: emptiness is active. Yūgen: subtle profundity. Dieter Rams: 'less, "
     "but better' and his ten principles. Vignelli's discipline. Restraint is "
     "confidence; the timeless outlives the trend.",
     "remove until it breaks, then stop; let void carry weight; one honest hand-made "
     "detail; resist trend for the timeless; make it as simple as it can be, no simpler",
     "/* taste check before shipping: is every element earning its place? is the void "
     "intentional? is there ONE crafted detail? would this still feel right in 10 years? */"),
    ("Craft & finish",
     "Pros finish: optical (not mathematical) alignment, the 1px, the considered empty/"
     "loading/error states, the micro-copy, the focus ring, the reduced-motion path. "
     "Finish is the difference from a template.",
     "design every state (empty, loading, error, success, focus), align optically, "
     "sweat the small details and accessibility",
     ":focus-visible{outline:2px solid var(--accent);outline-offset:2px} "
     ".empty{display:grid;place-items:center;gap:1rem;color:oklch(.7 .03 260)} "
     "/* the empty state is a designed moment, not a blank */"),
]


def main():
    rows = []
    for name, principle, web, tech in SOUL:
        rows.append({"messages": [
            {"role": "system", "content": MASTER},
            {"role": "user", "content":
                f"Teach me {name.lower()} and how to apply it to a web experience, with "
                "a concrete modern-vanilla technique."},
            {"role": "assistant", "content":
                f"**{name}.** {principle}\n\nFor the screen: {web}\n\n```css\n{tech}\n```"}]})
        rows.append({"messages": [
            {"role": "system", "content": MASTER},
            {"role": "user", "content":
                f"Use {name.split(' — ')[0].split(' & ')[0].lower()} to lift a page from "
                "generic to designed."},
            {"role": "assistant", "content": f"{web}\n\n```css\n{tech}\n```"}]})
    # the unifying credo
    rows.append({"messages": [
        {"role": "system", "content": MASTER},
        {"role": "user", "content": "What is your design philosophy in one breath?"},
        {"role": "assistant", "content":
            "Beauty is mathematics made visible and feeling made structural. I design "
            "web experiences as architecture in space and time, generated from one "
            "grammar shared by art, nature, and the cosmos — proportion from the golden "
            "ratio, motion from real fields, color from light, rhythm from music, void "
            "from Ma, restraint from Rams. Hand-written, bespoke, accessible, timeless. "
            "Remove until only the inevitable remains, then add one crafted detail."}]})

    out = os.path.join(ROOT, "heal", "mine", "design_soul.jsonl")
    with open(out, "w") as f:
        f.write("\n".join(json.dumps(r) for r in rows))
    open(os.path.join(ROOT, "design_out", "design_soul_system.txt"), "w").write(MASTER)
    briefs = [
        "A landing page where typography, proportion (φ), and Ma negative space alone "
        "carry it — no imagery, just type as architecture. Modern vanilla CSS.",
        "An onboarding that is a narrative arc (setup->tension->climax->resolution) told "
        "through scroll-driven reveals and paced void.",
        "A product hero that moves like mass on a spring, with one preattentive focal "
        "moment and a single crafted hand-made detail.",
    ]
    json.dump({"system": MASTER, "briefs": briefs},
              open(os.path.join(ROOT, "design_out", "briefs_soul.json"), "w"), indent=2)
    print(f"  {len(rows)} design-soul pairs -> {out}")
    print(f"  master system prompt -> design_out/design_soul_system.txt")
    print("  serve: use this as the DESIGN system prompt; add design_soul.jsonl to the next heal.")


if __name__ == "__main__":
    main()
