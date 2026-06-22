#!/usr/bin/env python3
"""Build the DESIGN-CANON heal source — the grammar of beauty as training data. A curated seed
of the masters' principles (design / architecture / color / typography) written as
(task -> principled, reasoned answer) pairs, so the model learns to *design like them and say
why*. The seed is real + GPU-free; --expand pulls extra design rows from the v4 corpus.
Output: heal/design/train.jsonl  (consumed by scripts/66_build_mixed_corpus.py as the `design` domain)

  python scripts/67_build_design_canon.py            # write the curated canon seed
  python scripts/67_build_design_canon.py --expand   # + design rows mined from heal/data-v4
"""
import argparse
import json
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "heal", "design")

# (prompt, principled answer) — the canon. Concise but real; expandable.
CANON = [
    ("What's the first thing to fix on a cluttered landing page?",
     "Remove, don't add. Dieter Rams: 'Good design is as little design as possible.' Cut every "
     "element that isn't doing work — decorative gradients, redundant copy, a third CTA. Clutter "
     "is unmade decisions. One clear focal point, generous negative space around it, and a single "
     "primary action. If removing something doesn't hurt the message, it was noise."),
    ("How should I set a type scale?",
     "Pick one ratio and commit. A modular scale (1.25 major-third or 1.333 perfect-fourth) gives "
     "sizes that relate by multiplication, not arbitrary px. Body 16–18px, then scale up for "
     "headings and down for captions off the ratio. Müller-Brockmann's lesson: hierarchy comes "
     "from *consistent* contrast, not from many sizes. Three to five steps is plenty."),
    ("My colors look muddy. How do I fix the palette?",
     "Work in OKLCH, not hex. Hold lightness and chroma constant and rotate hue for a harmonious "
     "set; vary lightness for tints/shades that stay perceptually even (sRGB hex doesn't — yellows "
     "read lighter than blues at the same value). Albers: color is relative — a swatch changes with "
     "its neighbor, so judge in context. One dominant, one accent, neutrals doing the heavy lifting."),
    ("How do I make a layout feel intentional, not random?",
     "Put it on a grid and respect a spacing rhythm. Choose a base unit (8px) and let all spacing "
     "be multiples — the eye reads the repetition as order. Align to columns; let things breathe on a "
     "consistent baseline. Josef Müller-Brockmann's grid systems: the grid is freedom, not a cage — "
     "it removes a thousand tiny decisions so you can spend attention where it matters."),
    ("What makes good contrast for accessibility AND beauty?",
     "They're the same goal. Body text ≥ 4.5:1 against its background, large text ≥ 3:1 (WCAG). But "
     "don't stop at pass/fail — contrast *is* hierarchy: the most important thing should have the most "
     "contrast, the least the least. Pure black on white is harsh; near-black (#111) on off-white "
     "reads calmer and still clears AA. Contrast is how you direct the eye."),
    ("How should motion feel in a UI?",
     "Motion should explain, not perform. Ease-out for things entering (fast then settle), ease-in for "
     "leaving; 150–250ms for most transitions — faster feels abrupt, slower feels sluggish. Animate "
     "transform and opacity (cheap, smooth), not layout. Disney's principles still apply: follow-through "
     "and anticipation make it feel alive; gratuitous motion makes it feel cheap."),
    ("What can architecture teach UI design?",
     "Proportion, light, and procession. Mies: 'God is in the details' — a join done right reads as "
     "care everywhere. Tadao Ando: light is a material; negative space isn't empty, it's *structure* "
     "you can feel. Kahn asked what a space 'wants to be.' A screen is a room: lead the eye through it "
     "in sequence, give the important thing air, and let the structure show."),
    ("How do I pick a typeface pairing?",
     "Contrast with a reason, then stop. One workhorse (a humanist sans like Inter for UI), optionally "
     "one voice face for display. Pair by contrast of structure (a sans + a serif) but harmony of "
     "proportion (similar x-height). Paul Rand: typography is the visual form of language — legibility "
     "first, personality second. Two families, used consistently, beat five used cleverly."),
    ("Critique this: a hero with a centered headline, a subhead, and two equal buttons.",
     "Two *equal* buttons is the bug — equal weight means no decision made for the user. Make the "
     "primary action solid and prominent, the secondary a quiet ghost/text link. Centered is fine for "
     "a short headline but breaks down past two lines (ragged center is hard to read) — left-align the "
     "subhead. And check the headline's measure: 45–75 characters per line, or the eye loses its place."),
    ("What's the Swiss/International style and when should I reach for it?",
     "Objective, grid-driven, typographic clarity — Müller-Brockmann, Hofmann, Akzidenz/Helvetica, "
     "asymmetric layouts on a strict grid, lots of white space, photography over illustration. Reach "
     "for it when the content is the message and you want timeless over trendy: dashboards, docs, "
     "editorial, brand systems. It ages well precisely because it refuses decoration."),
    ("How do I use whitespace well?",
     "Whitespace is the design, not the leftovers. Group related things tight and separate unrelated "
     "things with space (proximity = the Gestalt law doing your grouping for free). Macro space (margins, "
     "section gaps) sets calm and pace; micro space (line-height ~1.5, letter-spacing on caps) sets "
     "legibility. When in doubt, add more — crowded reads as cheap, spacious reads as considered."),
    ("Make a dark theme that doesn't look like inverted light.",
     "Don't use pure black (#000) or pure white text — it vibrates. Base on a very dark desaturated "
     "near-black (oklch ~18% L, slight hue), text at ~90% L not 100%. Reduce saturation of accents "
     "(bright colors glow on dark). Elevate surfaces with subtle lightness steps, not heavy borders. "
     "Shadows barely work on dark — use lighter surfaces to show depth. It should feel designed *for* "
     "dark, with its own contrast logic."),
]


def build(expand):
    rows = [{"messages": [{"role": "user", "content": q}, {"role": "assistant", "content": a}]}
            for q, a in CANON]
    if expand:
        v4 = os.path.join(ROOT, "heal", "data-v4", "train.jsonl")
        kw = re.compile(r"oklch|css|html|<div|color:|grid|typograph|font-|flex|layout|design|wcag|hsl|"
                        r"padding|margin|button|hero|landing", re.I)
        if os.path.exists(v4):
            for line in open(v4):
                try:
                    r = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                txt = json.dumps(r.get("messages", r))
                if kw.search(txt) and len(rows) < 1200:
                    rows.append(r)
    os.makedirs(OUT, exist_ok=True)
    nv = max(2, len(rows) // 20)
    open(os.path.join(OUT, "valid.jsonl"), "w").write("\n".join(json.dumps(r) for r in rows[:nv]))
    open(os.path.join(OUT, "train.jsonl"), "w").write("\n".join(json.dumps(r) for r in rows[nv:]))
    print(f"  design canon -> {OUT}: {len(rows)} rows ({len(CANON)} curated + {len(rows)-len(CANON)} mined)")
    return len(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--expand", action="store_true")
    build(ap.parse_args().expand)
