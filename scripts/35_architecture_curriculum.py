#!/usr/bin/env python3
"""Architecture curriculum -> training data. Most web design uses a graphic-design
eye (color/type/2D) but no ARCHITECT's eye (proportion, procession, scale, light,
materiality, structure, void, threshold) — which is why it feels cookie-cutter.
A scrolled, navigated app IS architecture: design in space and time. This builds
that eye INTO the model: principle -> web translation -> concrete vanilla
technique, across the canon (pyramids -> parametric Dubai), plus exemplar briefs
for self-play.

  python scripts/35_architecture_curriculum.py
-> heal/mine/architecture_design.jsonl  (+ briefs in design_out/briefs_architecture.json)
"""
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")

SYS = ("You are a designer who thinks like an architect. Web experiences are "
       "architecture in space and time — proportion, composition, scale, "
       "procession, light, materiality, structure, void, threshold. Translate "
       "architectural principles into hand-written HTML/CSS/vanilla-JS (modern: "
       "scroll-driven animations, View Transitions, :has(), subgrid, OKLCH). "
       "Bespoke and contextual over framework defaults.")

# principle: (architectural idea + canon, web translation, concrete technique)
PRINCIPLES = [
    ("Proportion & ratio",
     "Classical orders, Palladio's harmonic ratios, the golden section, Le "
     "Corbusier's Modulor — beauty from a consistent proportional system.",
     "A ratio-based type + space scale instead of arbitrary px. The whole UI "
     "harmonizes because every size derives from one ratio.",
     ":root{--ratio:1.5;--s0:1rem;--s1:calc(var(--s0)*var(--ratio));"
     "--s2:calc(var(--s1)*var(--ratio))} h1{font-size:var(--s2)} /* Modulor-style */"),
    ("Composition & massing",
     "How volumes balance — Wright's asymmetric Fallingwater cantilevers vs "
     "Palladio's symmetry. Visual weight, a clear focal point.",
     "Intentional asymmetric balance and one focal point per view, not a "
     "centered card. Weight distributed like a facade.",
     "main{display:grid;grid-template-columns:1.618fr 1fr} /* golden split, "
     "focal mass left */"),
    ("Scale & monumentality",
     "The pyramids' mass, a Gothic nave's height, the Chrysler Building's "
     "verticality — scale CONTRAST creates awe, then intimacy.",
     "A monumental hero (huge display type, generous void) that compresses into "
     "intimate, readable body — the drama is the contrast.",
     "h1{font-size:clamp(3rem,12vw,11rem);line-height:.9} .body{max-width:62ch} "
     "/* monument -> room */"),
    ("Procession / promenade",
     "Corbusier's promenade architecturale, the Gothic nave drawing the eye to "
     "the altar, the long approach to the pyramids — a choreographed journey.",
     "Scroll choreography: sections revealed in sequence, the eye led, "
     "transitions between 'rooms'. The page is walked, not dumped.",
     "@media (prefers-reduced-motion:no-preference){.reveal{animation:rise "
     "linear both;animation-timeline:view();animation-range:entry 10% cover 35%}}"),
    ("Light & shadow",
     "Chiaroscuro; Kahn — 'the sun never knew how great it was until it struck "
     "the side of a building'; Tadao Ando's concrete carved by light.",
     "A consistent light source and an elevation scale: depth via layered "
     "shadow + OKLCH lightness, never flat-everywhere or shadow-everywhere.",
     "--e1:0 1px 2px oklch(0 0 0/.2);--e3:0 8px 24px oklch(0 0 0/.18);"
     ".card{box-shadow:var(--e3)} /* one light source, ranked elevation */"),
    ("Materiality & tectonics",
     "Honesty of material — Brutalist béton brut, Mies's steel-and-glass, Kahn's "
     "'what do you want, brick?'. The structure is expressed, not faked.",
     "Honest surfaces: real texture/grain, restrained glass (backdrop-filter), "
     "components that look like what they are. No fake 3D skeuomorphism.",
     ".glass{backdrop-filter:blur(12px) saturate(1.2);background:oklch(1 0 0/.06);"
     "border:1px solid oklch(1 0 0/.12)} /* tectonic, restrained */"),
    ("Void & negative space",
     "Japanese 'ma', the cloister courtyard, the Pantheon's oculus — emptiness "
     "is active, it frames and lets things breathe.",
     "Whitespace as a designed material, not leftover. A measured line length, "
     "generous margins; the void gives weight to the content.",
     ".section{padding-block:clamp(4rem,12vh,10rem)} p{max-width:60ch} "
     "/* the void frames */"),
    ("Rhythm & repetition",
     "The colonnade, fenestration bays, an aqueduct's arches — repetition with "
     "a steady beat, varied to avoid monotony.",
     "A modular grid with consistent rhythm; repeated cards/rows on one beat, "
     "with deliberate accents that break it.",
     "grid-template-columns:repeat(auto-fit,minmax(min(18rem,100%),1fr));"
     "gap:var(--s1) /* steady bay rhythm */"),
    ("Structure & grid (the bones)",
     "The Chicago frame — the steel skeleton freed the facade; Sullivan's tall "
     "office building; structural honesty, the bay system.",
     "CSS grid as real structure with named lines/subgrid; the layout's bones "
     "are honest and legible, the 'curtain wall' hangs off them.",
     ".app{display:grid;grid-template-columns:[full-start] minmax(1rem,1fr) "
     "[main-start] min(70rem,100%) [main-end] minmax(1rem,1fr) [full-end]}"),
    ("Context / genius loci",
     "Wright's organic architecture; Fallingwater grown from its stream — a "
     "building answers its site, never a template dropped anywhere.",
     "Design tokens + layout derived from the brand/content (its 'site'), not a "
     "generic theme. THE antidote to cookie-cutter.",
     "/* derive the palette + scale from the content's own character, per project; "
     "no off-the-shelf Bootstrap/Tailwind defaults */"),
    ("Ornament & restraint",
     "Sullivan's ornament over 'form follows function'; Loos's 'Ornament and "
     "Crime'; Art Nouveau's organic line (Gaudí, Horta) vs Bauhaus stripping; "
     "Venturi's 'less is a bore'.",
     "One expressive, crafted detail per view — a custom rule, a flourish, a "
     "considered micro-interaction — against otherwise disciplined restraint.",
     "/* a single bespoke accent: a hand-tuned underline, an SVG flourish, one "
     "motion — not ornament everywhere */"),
    ("Threshold & transition",
     "The portal, the narthex, Wright's compression-then-release (a low entry "
     "into a soaring room) — arrival is staged.",
     "Staged arrival: load -> reveal, a tight nav releasing into an open hero, "
     "View Transitions between sections so movement has continuity.",
     "@view-transition{navigation:auto} /* continuity across 'rooms'; "
     "compress the nav, release the hero */"),
]

# era: (landmarks/architects, the principle, the web application)
MOVEMENTS = [
    ("Ancient — the Pyramids of Giza",
     "monumental geometry, permanence, solar alignment, pure mass",
     "bold geometric hero, timeless type, a sense of permanence and silence"),
    ("Gothic — Chartres, Notre-Dame",
     "verticality, light through stained glass, the nave's procession to the altar",
     "vertical drama, luminous OKLCH color, a guided downward scroll to a climax"),
    ("Renaissance — Palladio, Brunelleschi's dome",
     "harmonic proportion, symmetry, the centered plan",
     "proportional type/space systems, balanced grids, a calm central axis"),
    ("Art Nouveau — Gaudí, Horta, Mucha",
     "the organic whiplash line, nature, total work of art",
     "custom organic SVG curves, flowing non-rectilinear layout, botanical OKLCH"),
    ("Art Deco — Chrysler & Empire State, NYC setbacks",
     "geometric luxury, verticality, the zoning setback, metallic sheen",
     "geometric ornament, gold-on-black, strong verticals, stepped/setback sections"),
    ("Chicago School — Sullivan, the steel frame, Mies's 860 Lake Shore",
     "'form follows function', the structural frame, tasteful ornament",
     "honest structural grid (subgrid), Inter/Helvetica clarity, one crafted accent"),
    ("Bauhaus / Modernism — Mies 'less is more', Le Corbusier's 5 points",
     "the free facade, function, primary color, the curtain wall",
     "clean grids, functional minimalism, the hero image AS the curtain wall"),
    ("Brutalism — béton brut, Boston City Hall",
     "raw material honesty, bold heavy mass, exposed structure",
     "the 'brutalist web' done WELL: raw, mono, bold — but with real proportion"),
    ("Postmodern — Venturi, Michael Graves",
     "'less is a bore', play, irony, historical reference",
     "expressive, decorative, eclectic — but intentional, not random"),
    ("Deconstructivism / Parametric — Gehry, Zaha Hadid, Dubai's Burj Khalifa",
     "fluid non-orthogonal form, computational/parametric, soaring spectacle",
     "generative/parametric layout, fluid CSS shapes, scroll-morphing, the "
     "parametric facade as a generative canvas; Islamic geometric pattern systems"),
    ("Vernacular houses — Victorian, Greene & Greene Craftsman, Wright's Prairie",
     "craft, human-scale proportion, warm materiality, the porch as threshold",
     "craftsmanship in detail, warm materials, human-scale spacing, an inviting "
     "'porch' entry (the hero that welcomes, not shouts)"),
    ("Contemporary — biophilic & sustainable (BIG, Bosco Verticale)",
     "nature integration, daylight, wellness, performance",
     "calm palettes, restrained motion, biophilic imagery, performance as a "
     "design value (fast = sustainable)"),
]


def main():
    rows = []
    for name, arch, web, tech in PRINCIPLES:
        rows.append({"messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content":
                f"Explain the architectural principle of {name.lower()} and how to "
                "apply it to a web experience, with a concrete technique."},
            {"role": "assistant", "content":
                f"**{name}.** In architecture: {arch}\n\nFor a web experience: {web}"
                f"\n\nConcrete technique:\n```css\n{tech}\n```"}]})
        rows.append({"messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content":
                f"My page feels generic. Use {name.lower()} to make it feel designed."},
            {"role": "assistant", "content":
                f"Apply {name.lower()}: {web} Start here:\n```css\n{tech}\n```"}]})
    for era, principle, web in MOVEMENTS:
        rows.append({"messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content":
                f"Design a web experience in the spirit of {era}."},
            {"role": "assistant", "content":
                f"{era} — its essence is {principle}. Translate that to the screen: "
                f"{web}. Keep it bespoke and proportion-driven, not a framework theme."}]})

    out = os.path.join(ROOT, "heal", "mine", "architecture_design.jsonl")
    with open(out, "w") as f:
        f.write("\n".join(json.dumps(r) for r in rows))
    briefs = [f"Design an immersive web experience in the spirit of {era.split(' — ')[0]}: "
              f"{web}." for era, _p, web in MOVEMENTS]
    bout = os.path.join(ROOT, "design_out", "briefs_architecture.json")
    json.dump({"system": SYS, "briefs": briefs}, open(bout, "w"), indent=2)
    print(f"  {len(rows)} architecture pairs -> {out}")
    print(f"  {len(briefs)} architecture briefs -> {bout}")
    print("  add architecture_design.jsonl to 27_build_heal_data (next heal);")
    print("  feed briefs to 26_bestofn --mode design for architectural self-play.")


if __name__ == "__main__":
    main()
