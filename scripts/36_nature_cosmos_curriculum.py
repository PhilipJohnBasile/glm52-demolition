#!/usr/bin/env python3
"""Nature + math + cosmos curriculum -> training data. The keystone of the design
soul: beauty is mathematics made visible — the same grammar (golden ratio/angle,
log spirals, fractals, Voronoi, branching, flocking, waves, symmetry, reaction-
diffusion) recurs from the seashell to Gaudí's columns to the spiral galaxy. This
teaches the model that grammar AS runnable vanilla-JS generative algorithms, so
it can design from the source of beauty rather than from templates. Ties together
art (31), architecture (35), and the creative-coding capability.

  python scripts/36_nature_cosmos_curriculum.py
-> heal/mine/nature_cosmos_design.jsonl  (+ design_out/briefs_nature.json)
"""
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")

SYS = ("You are a designer who sees beauty as mathematics made visible: the golden "
       "ratio and 137.5° golden angle, logarithmic spirals, fractals and self-"
       "similarity, Voronoi cells, L-system branching, flocking/emergence, wave "
       "interference, symmetry, and reaction-diffusion recur from the nautilus to "
       "Gaudí's columns to the spiral galaxy. Design immersive web experiences that "
       "tap this shared generative grammar of nature, art, architecture, and the "
       "cosmos — hand-written vanilla JS (Canvas/WebGL/SVG), OKLCH palettes drawn "
       "from natural and celestial light, proportion-driven, generative, alive. "
       "Never a framework template.")

# (phenomenon + the math + where else it appears, web translation, vanilla-JS technique)
NATURE = [
    ("Golden ratio & the Fibonacci spiral",
     "φ=1.618 in the nautilus, sunflower, and the arms of a spiral galaxy; the "
     "logarithmic spiral r=a·e^(bθ) is growth that keeps its shape.",
     "proportion systems + a spiral motif that organizes a hero or a radial menu",
     "const PHI=1.618; // log spiral\nfor(let t=0;t<8*Math.PI;t+=.05){"
     "const r=4*Math.exp(0.15*t);ctx.lineTo(cx+r*Math.cos(t),cy+r*Math.sin(t));}"),
    ("Phyllotaxis — the golden angle",
     "137.5° (the golden angle) packs sunflower seeds and pinecone scales with no "
     "gaps and no preferred direction — nature's optimal even distribution.",
     "the most beautiful way to scatter N elements (dots, cards on a radial, "
     "particles) — even, organic, never gridded",
     "const G=Math.PI*(3-Math.sqrt(5)); // 137.5°\nfor(let i=0;i<n;i++){"
     "const a=i*G,r=c*Math.sqrt(i);plot(cx+r*Math.cos(a),cy+r*Math.sin(a));}"),
    ("Fractals & self-similarity",
     "ferns, coastlines, Romanesco, lightning, river deltas — detail repeats "
     "across scales (fractal Brownian motion sums octaves of noise).",
     "scale-invariant texture, recursive layouts, organic backgrounds that hold "
     "detail at any zoom",
     "function fbm(x,y){let v=0,a=.5,f=1;for(let o=0;o<5;o++){"
     "v+=a*noise(x*f,y*f);f*=2;a*=.5;}return v;}"),
    ("Voronoi & Delaunay",
     "dragonfly wings, soap foam, giraffe coats, cracked earth, and the cosmic "
     "web of galaxies — space partitioned by nearest seed.",
     "organic tessellation, generative cell patterns, natural-feeling dividers "
     "and mosaics",
     "// nearest-seed cell per point\nlet best=1e9,id=0;seeds.forEach((s,k)=>{"
     "const d=(x-s.x)**2+(y-s.y)**2;if(d<best){best=d;id=k;}});"),
    ("L-systems & branching",
     "trees, lungs, blood vessels, rivers, lightning — recursive growth from a "
     "rewrite rule (F -> FF+[+F-F-F]-[-F+F+F]) drawn by a turtle.",
     "generative growth motifs, dendritic navigation, organic connectors that "
     "feel grown, not drawn",
     "let s='F';for(let i=0;i<4;i++)s=s.replace(/F/g,'FF+[+F-F]-[-F+F]');"
     "// then turtle: F=forward, +/- = turn ±25°, [ ]=push/pop"),
    ("Flocking & emergence (boids)",
     "starling murmurations, fish schools, ant trails — three local rules "
     "(separation, alignment, cohesion) produce complex collective beauty.",
     "living particle systems whose motion feels alive and intentional",
     "v=v.add(sep(b).mul(1.5)).add(align(b)).add(cohere(b)); // per boid; "
     "complexity emerges from simple neighborhood rules"),
    ("Reaction-diffusion (Turing patterns)",
     "leopard spots, coral, seashell pigment, fingerprints — two chemicals "
     "diffusing+reacting (Gray-Scott) self-organize into organic patterns.",
     "generative organic textures and surfaces that look biological, not noisy",
     "a += Da*lap(a) - a*b*b + f*(1-a);\nb += Db*lap(b) + a*b*b - (k+f)*b; "
     "// Gray-Scott, per cell per tick"),
    ("Waves & interference",
     "water ripples, dunes, sound, light, the ridges of a shell — superposed "
     "sinusoids; interference makes moiré and caustics.",
     "flow fields, rippling reflections, undulating type or grids, caustic light",
     "const h=(x,y,t)=>Math.sin(x*.04+t)+Math.sin(y*.03-t*.7)"
     "+Math.sin((x+y)*.02+t*.4); // sum-of-sines height field"),
    ("Symmetry & tessellation",
     "snowflakes (6-fold), honeycombs (hexagonal packing), crystals, and Islamic "
     "girih patterns — the wallpaper symmetry groups tile the plane.",
     "kaleidoscopic motifs, hex grids, generative geometric pattern systems",
     "ctx.translate(cx,cy);for(let i=0;i<6;i++){ctx.rotate(Math.PI/3);"
     "drawWedge();} // 6-fold snowflake symmetry"),
    ("Color in nature",
     "structural iridescence (butterfly wings, opal), Rayleigh-scattered sky, "
     "sunsets, bioluminescence, the aurora — light as physics, not swatches.",
     "OKLCH palettes sampled from real phenomena; iridescence by view angle; a "
     "sky that shifts hue with 'time'",
     "// thin-film iridescence: hue from angle\nconst hue=(angle*180/Math.PI*2)%360;"
     "el.style.color=`oklch(0.8 0.18 ${hue})`;"),
]

COSMOS = [
    ("Celestial mechanics & resonance",
     "Kepler's orbits and orbital resonance (Jupiter's moons 1:2:4) — the "
     "'music of the spheres', harmonic timing in motion.",
     "orbital motion and harmonically-timed animation (durations in small-integer "
     "ratios feel composed, not random)",
     "const T=base*ratio; // resonant periods 1:2:4\n"
     "x=cx+a*Math.cos(2*Math.PI*t/T); y=cy+b*Math.sin(2*Math.PI*t/T);"),
    ("Spiral galaxies & the cosmic web",
     "density-wave logarithmic arms; the universe's largest structure is a "
     "Voronoi-like web of filaments and voids.",
     "generative cosmic structure — spiral arms, filament networks as a living "
     "backdrop",
     "for(let i=0;i<N;i++){const t=i*0.1,arm=i%2*Math.PI;"
     "const r=t*8,a=t*0.4+arm;star(cx+r*Math.cos(a),cy+r*Math.sin(a));}"),
    ("Scale & the sublime",
     "powers of ten from quark to cosmic web (~10^40); the awe of scale is a "
     "designable emotion.",
     "zoom/scale experiences, dramatic scale contrast (the monumental into the "
     "intimate), the sublime of bigness",
     "// logarithmic zoom: each step multiplies scale\nscale*=Math.pow(10,dt*0.2);"),
    ("Starlight, nebulae, deep field",
     "emission spectra color nebulae; additive light builds glow and depth; the "
     "Hubble Deep Field — luminous dark.",
     "luminous OKLCH on near-black, additive glow, layered depth, restraint so "
     "light reads as light",
     "ctx.globalCompositeOperation='lighter'; // additive starlight\n"
     "halo('oklch(0.9 0.15 95 / .3)'); core('oklch(0.97 0.05 100)');"),
    ("The night sky & wayfinding",
     "constellations and celestial navigation — humanity's oldest interface; the "
     "sky as a map and a story.",
     "star maps, wayfinding, a felt human relationship to the cosmos; orientation "
     "as narrative",
     "// connect named stars into a constellation path the user can trace\n"
     "stars.forEach((s,i)=>i?ctx.lineTo(s.x,s.y):ctx.moveTo(s.x,s.y));"),
]


def main():
    rows = []
    blocks = [("nature", NATURE), ("cosmos", COSMOS)]
    for kind, table in blocks:
        for name, math_, web, tech in table:
            rows.append({"messages": [
                {"role": "system", "content": SYS},
                {"role": "user", "content":
                    f"How do I bring {name.lower()} into a web experience? Show the math "
                    "and a vanilla-JS technique."},
                {"role": "assistant", "content":
                    f"**{name}.** The pattern: {math_}\n\nIn an interface: {web}\n\n"
                    f"```js\n{tech}\n```"}]})
    # synthesis: the unifying thesis — merge nature with art + architecture
    rows.append({"messages": [
        {"role": "system", "content": SYS},
        {"role": "user", "content":
            "Why do nature, art, architecture, and the cosmos feel connected, and how "
            "should that shape what I build?"},
        {"role": "assistant", "content":
            "Because they share one grammar — beauty is mathematics made visible. The "
            "golden angle packs a sunflower and spirals a galaxy; the logarithmic "
            "spiral is a nautilus, a hurricane, and a galaxy's arm; Voronoi is a "
            "dragonfly wing and the cosmic web; Gaudí grew columns from trees; van "
            "Gogh painted turbulent flow before physics could. Build from that source: "
            "derive proportion from φ, motion from real fields (flow, orbits, waves), "
            "texture from fractals and reaction-diffusion, color from natural and "
            "celestial light — generative and proportion-driven, never a template. "
            "Then the app feels inevitable, the way a shell or a cathedral does."}]})

    out = os.path.join(ROOT, "heal", "mine", "nature_cosmos_design.jsonl")
    with open(out, "w") as f:
        f.write("\n".join(json.dumps(r) for r in rows))
    briefs = [
        "Be inside a sunflower's phyllotaxis becoming a spiral galaxy — 137.5° seeds "
        "that bloom outward into stars. Vanilla JS + Canvas, OKLCH gold-to-cosmic.",
        "Be inside a living reef of reaction-diffusion coral, slowly growing, "
        "bioluminescent OKLCH, the pattern responds to the pointer.",
        "Be inside a starling murmuration at dusk — boids flocking over fields, the "
        "flock answers your cursor, OKLCH dusk palette.",
        "Be inside a fractal forest grown by an L-system, branches swaying, light "
        "filtering through, OKLCH dawn.",
        "Be inside the cosmic web — Voronoi filaments of galaxies and dark voids, "
        "slow drift, additive starlight, the sublime of scale.",
        "Be inside an aurora driven by wave interference over a tundra, OKLCH "
        "green-violet, ribbons following the magnetic field and the pointer.",
    ]
    bout = os.path.join(ROOT, "design_out", "briefs_nature.json")
    json.dump({"system": SYS, "briefs": briefs}, open(bout, "w"), indent=2)
    print(f"  {len(rows)} nature+cosmos pairs -> {out}")
    print(f"  {len(briefs)} nature/cosmos briefs -> {bout}")
    print("  unifies art(31)+architecture(35)+nature(36) = the design soul; "
          "add all three to 27_build_heal_data for the next heal.")


if __name__ == "__main__":
    main()
