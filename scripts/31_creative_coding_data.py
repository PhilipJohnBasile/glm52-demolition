#!/usr/bin/env python3
"""Build the CREATIVE-CODING / generative-art capability into the model — the
'be the world inside the painting' genre our design data was missing (it was
UI/landing-page only). Two outputs:

  (1) heal/mine/creative_coding.jsonl  — GOLD pairs: art-directed brief -> a
      single self-contained immersive HTML (Canvas/WebGL/SVG + vanilla JS, OKLCH
      from the subject's palette, hand-built motion). Seeded from
      design_out/exemplars/. These teach the FORM. (Authoring gold training data
      is capability-building; the model — not Claude — generates at inference.)
  (2) design_out/briefs_creative.json — the art-directed brief SET for self-play:
      once served, `26_bestofn.py --mode design` generates N per brief, the
      render-critique loop (25) measures them, and the best become new training
      data -> next heal. That self-play is how the capability scales without
      hand-authoring every scene.

  python scripts/31_creative_coding_data.py
"""
import glob
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
EXEMPLARS = os.path.join(ROOT, "design_out", "exemplars")

GENRE = (
    "You are a generative / creative-coding designer. Build a SINGLE "
    "self-contained HTML document — no framework, no external libraries — that "
    "does NOT depict the subject but puts the viewer INSIDE its world: an "
    "immersive, animated, art-directed scene. Use Canvas/WebGL/SVG with "
    "hand-written vanilla JS; an OKLCH palette pulled from the subject's actual "
    "colors; hand-built motion (flow fields, particle brushstrokes, impasto, "
    "curl noise) rather than canned easing; meaningful interactivity; "
    "prefers-reduced-motion support; and accessible semantics (a descriptive "
    "label, real text). Favor bespoke composition over centered-card, "
    "framework-default layouts. The result should feel painted and alive."
)

# brief for each shipped exemplar (gold). Add a sidecar <name>.brief.txt for new ones.
EXEMPLAR_BRIEFS = {
    "starry_night_world.html":
        "Build an app that is NOT a copy of Van Gogh's Starry Night but the WORLD "
        "inside it: Saint-Rémy at night, a swirling sky the viewer can stir with "
        "the cursor, eleven burning impasto stars and a crescent moon, a sleeping "
        "village with flickering windows and a tall church spire, and the great "
        "flame-cypress in the foreground. Vanilla JS + Canvas, OKLCH Van Gogh "
        "palette, no framework.",
}

# the art-directed brief SET (self-play targets; the gold one is included).
BRIEFS = [
    EXEMPLAR_BRIEFS["starry_night_world.html"],
    "Be the world inside Hokusai's Great Wave: under the curling crest, fractal "
    "foam, Mount Fuji small and calm beyond. Vanilla JS + Canvas, OKLCH indigo/"
    "foam-white palette, the wave responds to scroll.",
    "Be the world inside Klimt's The Kiss: a field of gold leaf and ornament the "
    "viewer drifts through, warm metallic OKLCH, light catching the patterns.",
    "Be inside a Rothko color field: breathing luminous stacked rectangles, edges "
    "feathered, meditative slow drift, OKLCH, reduced-motion = a still painting.",
    "Be the world inside Monet's water lilies at dusk: rippling reflections, koi "
    "moving under the surface, pads, OKLCH lavender/green, cursor makes ripples.",
    "Be inside a living aurora over a tundra at night: magnetic ribbons of green "
    "and violet, a field of stars, snow, OKLCH, the ribbons answer the pointer.",
    "Be inside a bioluminescent deep sea: drifting plankton, slow current, a "
    "distant whale silhouette, OKLCH cyan/abyss-blue, click to scatter light.",
    "Be inside a Turner seascape storm: light breaking through spray and cloud, "
    "a half-seen ship, OKLCH warm-grey/gold, motion of weather.",
    "Be a generative Provençal lavender field at golden hour: wind moving in rows, "
    "bees, distant hills, OKLCH lavender/ochre, the wind follows the cursor.",
    "Be inside Mondrian's Broadway Boogie-Woogie as a city at night: neon blocks, "
    "traffic pulses moving along the grid, OKLCH primaries on black.",
]


def main():
    pairs = []
    for path in sorted(glob.glob(os.path.join(EXEMPLARS, "*.html"))):
        name = os.path.basename(path)
        side = path[:-5] + ".brief.txt"
        brief = (open(side).read().strip() if os.path.exists(side)
                 else EXEMPLAR_BRIEFS.get(name))
        if not brief:
            print(f"  [skip] {name}: no brief (add {os.path.basename(side)})")
            continue
        html = open(path).read()
        pairs.append({"messages": [
            {"role": "system", "content": GENRE},
            {"role": "user", "content": brief},
            {"role": "assistant", "content": f"```html\n{html}\n```"}]})
        print(f"  gold pair <- {name} ({len(html)} bytes)")

    out = os.path.join(ROOT, "heal", "mine", "creative_coding.jsonl")
    with open(out, "w") as f:
        f.write("\n".join(json.dumps(p) for p in pairs))
    briefs_out = os.path.join(ROOT, "design_out", "briefs_creative.json")
    json.dump({"system": GENRE, "briefs": BRIEFS}, open(briefs_out, "w"), indent=2)
    print(f"\n  {len(pairs)} gold pair(s) -> {out}")
    print(f"  {len(BRIEFS)} self-play briefs -> {briefs_out}")
    print("  next: serve model, then for each brief run "
          "`26_bestofn.py --mode design` -> keep low-findings renders as new "
          "training data (self-play); add more gold exemplars over time.")


if __name__ == "__main__":
    main()
