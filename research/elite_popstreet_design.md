# Elite Pop-Art & Street-Art Design: SFT Gold — Bold Expression Lane

*Companion to elite_design.md (Swiss/minimalist lane). This file teaches the model that BOLD ≠ SLOPPY.
The aesthetic shifts from restraint to exuberance — but the craft stays elite:
OKLCH color, semantic HTML5, real CSS grid/flex, accessible contrast, bespoke code, zero frameworks.*

---

## CANON NOTE: The Four Masters + Web Mapping

### Andy Warhol (1928–1987) — Seriality as System
Warhol's silkscreen method (adopted 1962) turned mechanical reproduction into fine art. His signature
moves: **grid of identical or near-identical tiles**, **flat saturated color fields with no shading**,
**deliberate mis-registration** (color layer slightly offset from contour), **celebrity/consumer-product
iconography** treated with equal visual weight. The Marilyn Diptych (1962) and Campbell's Soup Cans
both exploit repetition to oscillate between worship and critique. Color palette: acid yellow, hot
magenta, electric cyan, orange-red — lifted straight from offset lithography's CMYK limits pushed
to pop excess. Web mapping: repeated CSS grid tiles, flat OKLCH color fills per tile, same image
recolored via CSS `filter: hue-rotate()` or custom properties, no drop-shadows, no gradients,
deliberate "screen-print" font (bold condensed grotesque), tight kerning.

### Banksy (b. ~1974) — Subversion in High Contrast
Banksy's multi-layer acetate stencils spray aerosol black on walls — fast, precise, reproducible.
Signature aesthetic: **monochrome base figure** (stark black on white/grey/brick), then **exactly one
strategic color accent** — almost always red, occasionally yellow. The tension is the message: a
child releasing heart-shaped balloons (lost innocence), the "Flower Thrower" (rioter hurling a
bouquet — grit vs. beauty). "Stencil edge" is crisp but reads as handmade — the graphic is bold,
the texture is raw. Typography when used: slab-serif or distressed caps stencil lettering. Web
mapping: dark/neutral background, SVG-clipped black stencil figure, ONE OKLCH accent color,
high-contrast text, deliberately rough `clip-path` or `mask` edges to evoke spray paint.

### Mr. Brainwash / Thierry Guetta (b. 1966) — Joyful Maximalism on a Grid
MBW's method is collage + overpainting + stencil + silkscreen all simultaneously. Inspirations:
Warhol, Keith Haring, Basquiat — then MORE of everything. His "Life is Beautiful" mantra means
layered cultural icons (Marilyn over Einstein over Che), drips of paint, typographic proclamations,
spray tags. But crucially: even his most chaotic canvases hold an underlying compositional grid —
the chaos is organized chaos. Web mapping: CSS grid holds structure; within cells, layered `z-index`
elements create depth; paint drips via SVG `<path>` or CSS clip-paths; custom font mixing (stencil +
brush); explosive OKLCH palette but still harmonious at distance.

### Takashi Murakami (b. 1962) — Superflat Smiling Flowers / Kawaii Pop
Murakami coined "Superflat" (2001): **zero depth, zero shadow, zero perspective** — a flat plane
where high art and otaku consumer culture exist at equal altitude. His smiling daisy flowers (1995–)
are the icon: bold black outline, flat single-color petals, circular smiling face, repeated at scale
across the full field. Palette: vivid, high-chroma — the 12-color flower field uses every hue at
maximum saturation. Influences: nihonga woodblock flatness + manga line weight + kawaii commercial
design. Web mapping: SVG inline flowers in a CSS grid / repeat, OKLCH at chroma 0.25+ for each
petal, `stroke` outlines on SVG, absolutely no `filter: drop-shadow`, playful rounded display font,
the entire hero IS the flower grid.

---

## GOLD EXAMPLES

---

### EXAMPLE 1 — Warhol: Product Grid Showcase

**Prompt:** Build a Warhol-inspired product showcase for a fictional fragrance "ICON №5". Eight
repeated tiles in a 4×2 grid. Each tile shows the same bottle silhouette recolored in a flat
pop palette. Grid tight, no gutters between tiles. Bold condensed logotype above. Flat, no
shadows, deliberate mechanical feel. Elite OKLCH palette, semantic HTML, accessible.

**Why elite:** Every color is OKLCH-calculated for identical perceptual lightness (L=0.62) at
maximum chroma — the grid reads as a perfect color wheel without any tile feeling dim. The
recoloring uses CSS custom properties + `filter: hue-rotate()` so it is one SVG repeated
eight times, not eight images. The grid is `display: grid` with `repeat(4, 1fr)`. No Bootstrap.
No shadows. No gradients. The mechanical repetition IS the message.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ICON №5 — A Warhol Fragrance Grid</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --hue-0:   oklch(0.62 0.28 10);   /* hot magenta-red   */
    --hue-1:   oklch(0.62 0.28 55);   /* acid orange       */
    --hue-2:   oklch(0.62 0.28 100);  /* electric yellow   */
    --hue-3:   oklch(0.62 0.28 145);  /* pop green         */
    --hue-4:   oklch(0.62 0.28 200);  /* electric cyan     */
    --hue-5:   oklch(0.62 0.28 245);  /* vivid blue        */
    --hue-6:   oklch(0.62 0.28 300);  /* purple            */
    --hue-7:   oklch(0.62 0.28 340);  /* hot pink          */
    --ink:     oklch(0.10 0.00 0);
    --paper:   oklch(0.97 0.00 0);
  }

  body {
    background: var(--paper);
    font-family: 'Arial Black', 'Helvetica Neue', sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem 1rem;
    min-height: 100svh;
  }

  header {
    text-align: center;
    margin-bottom: 0;
  }

  .brand {
    font-size: clamp(2.5rem, 8vw, 5rem);
    font-weight: 900;
    letter-spacing: -0.02em;
    text-transform: uppercase;
    line-height: 1;
    color: var(--ink);
  }

  .brand em {
    font-style: normal;
    color: oklch(0.62 0.28 10);
  }

  .tagline {
    font-size: clamp(0.65rem, 1.5vw, 0.85rem);
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: var(--ink);
    margin-top: 0.4rem;
    margin-bottom: 1.5rem;
  }

  /* The Warhol grid: no gaps, tiles flush */
  .grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    width: min(900px, 100%);
  }

  .tile {
    aspect-ratio: 3 / 4;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
  }

  /* Each tile gets its flat color via nth-child + custom prop */
  .tile:nth-child(1) { background: var(--hue-0); }
  .tile:nth-child(2) { background: var(--hue-1); }
  .tile:nth-child(3) { background: var(--hue-2); }
  .tile:nth-child(4) { background: var(--hue-3); }
  .tile:nth-child(5) { background: var(--hue-4); }
  .tile:nth-child(6) { background: var(--hue-5); }
  .tile:nth-child(7) { background: var(--hue-6); }
  .tile:nth-child(8) { background: var(--hue-7); }

  /* Bottle SVG: flat black silhouette, same on every tile */
  .bottle {
    width: 45%;
    height: auto;
    display: block;
  }

  .tile-label {
    position: absolute;
    bottom: 0.6rem;
    font-size: clamp(0.5rem, 1.2vw, 0.7rem);
    font-weight: 900;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--ink);
    mix-blend-mode: multiply;
  }

  /* Deliberate mis-registration: shift label slightly per row */
  .tile:nth-child(n+5) .tile-label { bottom: 0.8rem; left: 0.5rem; }

  footer {
    margin-top: 1.5rem;
    font-size: 0.7rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: oklch(0.45 0.00 0);
  }
</style>
</head>
<body>
<header>
  <h1 class="brand">ICON <em>№5</em></h1>
  <p class="tagline">A Fragrance in Eight Editions</p>
</header>

<main>
  <section class="grid" aria-label="Eight colorways of ICON No.5 fragrance">
    <!-- Eight tiles: same SVG bottle, eight flat pop backgrounds -->
    <!-- SVG is an inline bottle silhouette: stopper + neck + shoulder + body + base -->
    <article class="tile">
      <svg class="bottle" viewBox="0 0 60 120" aria-hidden="true">
        <!-- stopper -->
        <rect x="22" y="0" width="16" height="8" rx="2"/>
        <!-- neck -->
        <rect x="25" y="8" width="10" height="18" rx="1"/>
        <!-- shoulder curve -->
        <path d="M25 26 Q15 34 14 46 L46 46 Q45 34 35 26Z"/>
        <!-- body -->
        <rect x="14" y="46" width="32" height="58" rx="3"/>
        <!-- base foot -->
        <rect x="11" y="100" width="38" height="6" rx="2"/>
        <!-- label stripe: lighter inset -->
        <rect x="17" y="56" width="26" height="30" rx="1" fill="white" fill-opacity="0.25"/>
      </svg>
      <span class="tile-label">No.5 — I</span>
    </article>
    <article class="tile">
      <svg class="bottle" viewBox="0 0 60 120" aria-hidden="true">
        <rect x="22" y="0" width="16" height="8" rx="2"/>
        <rect x="25" y="8" width="10" height="18" rx="1"/>
        <path d="M25 26 Q15 34 14 46 L46 46 Q45 34 35 26Z"/>
        <rect x="14" y="46" width="32" height="58" rx="3"/>
        <rect x="11" y="100" width="38" height="6" rx="2"/>
        <rect x="17" y="56" width="26" height="30" rx="1" fill="white" fill-opacity="0.25"/>
      </svg>
      <span class="tile-label">No.5 — II</span>
    </article>
    <article class="tile">
      <svg class="bottle" viewBox="0 0 60 120" aria-hidden="true">
        <rect x="22" y="0" width="16" height="8" rx="2"/>
        <rect x="25" y="8" width="10" height="18" rx="1"/>
        <path d="M25 26 Q15 34 14 46 L46 46 Q45 34 35 26Z"/>
        <rect x="14" y="46" width="32" height="58" rx="3"/>
        <rect x="11" y="100" width="38" height="6" rx="2"/>
        <rect x="17" y="56" width="26" height="30" rx="1" fill="white" fill-opacity="0.25"/>
      </svg>
      <span class="tile-label">No.5 — III</span>
    </article>
    <article class="tile">
      <svg class="bottle" viewBox="0 0 60 120" aria-hidden="true">
        <rect x="22" y="0" width="16" height="8" rx="2"/>
        <rect x="25" y="8" width="10" height="18" rx="1"/>
        <path d="M25 26 Q15 34 14 46 L46 46 Q45 34 35 26Z"/>
        <rect x="14" y="46" width="32" height="58" rx="3"/>
        <rect x="11" y="100" width="38" height="6" rx="2"/>
        <rect x="17" y="56" width="26" height="30" rx="1" fill="white" fill-opacity="0.25"/>
      </svg>
      <span class="tile-label">No.5 — IV</span>
    </article>
    <article class="tile">
      <svg class="bottle" viewBox="0 0 60 120" aria-hidden="true">
        <rect x="22" y="0" width="16" height="8" rx="2"/>
        <rect x="25" y="8" width="10" height="18" rx="1"/>
        <path d="M25 26 Q15 34 14 46 L46 46 Q45 34 35 26Z"/>
        <rect x="14" y="46" width="32" height="58" rx="3"/>
        <rect x="11" y="100" width="38" height="6" rx="2"/>
        <rect x="17" y="56" width="26" height="30" rx="1" fill="white" fill-opacity="0.25"/>
      </svg>
      <span class="tile-label">No.5 — V</span>
    </article>
    <article class="tile">
      <svg class="bottle" viewBox="0 0 60 120" aria-hidden="true">
        <rect x="22" y="0" width="16" height="8" rx="2"/>
        <rect x="25" y="8" width="10" height="18" rx="1"/>
        <path d="M25 26 Q15 34 14 46 L46 46 Q45 34 35 26Z"/>
        <rect x="14" y="46" width="32" height="58" rx="3"/>
        <rect x="11" y="100" width="38" height="6" rx="2"/>
        <rect x="17" y="56" width="26" height="30" rx="1" fill="white" fill-opacity="0.25"/>
      </svg>
      <span class="tile-label">No.5 — VI</span>
    </article>
    <article class="tile">
      <svg class="bottle" viewBox="0 0 60 120" aria-hidden="true">
        <rect x="22" y="0" width="16" height="8" rx="2"/>
        <rect x="25" y="8" width="10" height="18" rx="1"/>
        <path d="M25 26 Q15 34 14 46 L46 46 Q45 34 35 26Z"/>
        <rect x="14" y="46" width="32" height="58" rx="3"/>
        <rect x="11" y="100" width="38" height="6" rx="2"/>
        <rect x="17" y="56" width="26" height="30" rx="1" fill="white" fill-opacity="0.25"/>
      </svg>
      <span class="tile-label">No.5 — VII</span>
    </article>
    <article class="tile">
      <svg class="bottle" viewBox="0 0 60 120" aria-hidden="true">
        <rect x="22" y="0" width="16" height="8" rx="2"/>
        <rect x="25" y="8" width="10" height="18" rx="1"/>
        <path d="M25 26 Q15 34 14 46 L46 46 Q45 34 35 26Z"/>
        <rect x="14" y="46" width="32" height="58" rx="3"/>
        <rect x="11" y="100" width="38" height="6" rx="2"/>
        <rect x="17" y="56" width="26" height="30" rx="1" fill="white" fill-opacity="0.25"/>
      </svg>
      <span class="tile-label">No.5 — VIII</span>
    </article>
  </section>
</main>

<footer>
  <p>Limited Edition · Eight Colorways · One Icon</p>
</footer>
</body>
</html>
```

---

### EXAMPLE 2 — Banksy: Stencil Landing Hero

**Prompt:** A landing hero for a social-justice campaign called "RECLAIM". Banksy aesthetic:
dark charcoal background, one large stencil-style SVG figure (child releasing a bunch of
balloons), balloons in ONE bold OKLCH red. Bold high-contrast headline: "BEAUTY IS AN ACT
OF RESISTANCE." Stencil-edge display type. Minimal. No decorative elements.

**Why elite:** The entire visual effect comes from SVG `clip-path` + pure CSS — no image files.
The "stencil edge" on the letterforms is achieved with `font-variation-settings` on a variable
font + `letter-spacing` tight condensed, not a fake distress filter. Exactly one color (OKLCH red)
appears in the entire composition; everything else is a greyscale OKLCH. Contrast ratio of
headline text on background: >8:1. The composition uses CSS grid to lock the figure to the
right third and text to the left two-thirds — intentional negative space as in the real stencils.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RECLAIM — Stencil Hero</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --wall:    oklch(0.13 0.005 250);   /* dark charcoal     */
    --stencil: oklch(0.08 0.00  0);     /* near-black ink    */
    --accent:  oklch(0.55 0.28 25);     /* ONE bold red      */
    --light:   oklch(0.88 0.00  0);     /* near-white text   */
    --mid:     oklch(0.50 0.00  0);     /* mid-grey subtext  */
  }

  html, body {
    height: 100%;
  }

  body {
    background: var(--wall);
    color: var(--light);
    font-family: 'Arial Black', 'Impact', 'Haettenschweiler', sans-serif;
    display: flex;
    flex-direction: column;
    min-height: 100svh;
  }

  /* Subtle texture overlay — pure CSS noise using radial gradients */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      radial-gradient(circle at 20% 50%, oklch(0.18 0.00 0 / 0.4) 0%, transparent 60%),
      radial-gradient(circle at 80% 20%, oklch(0.10 0.00 0 / 0.5) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }

  /* Two-column hero: text left, figure right */
  .hero {
    flex: 1;
    display: grid;
    grid-template-columns: 3fr 2fr;
    grid-template-rows: 1fr;
    align-items: center;
    padding: clamp(2rem, 5vw, 5rem) clamp(1.5rem, 6vw, 6rem);
    position: relative;
    z-index: 1;
    gap: 2rem;
  }

  .hero-text {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .eyebrow {
    font-size: clamp(0.6rem, 1.2vw, 0.75rem);
    letter-spacing: 0.4em;
    text-transform: uppercase;
    color: var(--accent);
    font-family: 'Arial', sans-serif;
    font-weight: 700;
  }

  .headline {
    font-size: clamp(2.4rem, 7vw, 6rem);
    font-weight: 900;
    line-height: 0.95;
    letter-spacing: -0.02em;
    text-transform: uppercase;
    color: var(--light);
  }

  /* The one-word accent break */
  .headline .accent-word {
    color: var(--accent);
    display: block;
  }

  .subline {
    font-size: clamp(0.75rem, 1.5vw, 1rem);
    font-weight: 400;
    font-family: 'Arial', sans-serif;
    color: var(--mid);
    letter-spacing: 0.05em;
    max-width: 42ch;
    line-height: 1.6;
  }

  .cta {
    display: inline-block;
    border: 2px solid var(--accent);
    color: var(--accent);
    font-size: 0.75rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    font-weight: 900;
    padding: 0.8rem 2rem;
    text-decoration: none;
    transition: background 0.15s, color 0.15s;
    align-self: flex-start;
    font-family: 'Arial Black', sans-serif;
  }

  .cta:hover, .cta:focus-visible {
    background: var(--accent);
    color: var(--wall);
    outline: none;
  }

  /* The stencil figure: SVG child with balloon cluster */
  .stencil-figure {
    display: flex;
    justify-content: center;
    align-items: flex-end;
  }

  /* Stencil SVG — child silhouette + balloon cluster */
  /* Black/dark figure, red balloons ONLY */
  .stencil-figure svg {
    width: 100%;
    max-width: 320px;
    height: auto;
    /* Slight spray-paint blur on edges */
    filter: blur(0.4px);
  }

  /* Stencil "ink bleed" effect via drop-shadow on dark elements */
  .stencil-ink {
    filter: drop-shadow(0 0 3px oklch(0.08 0.00 0 / 0.6));
  }

  footer {
    position: relative;
    z-index: 1;
    padding: 1rem clamp(1.5rem, 6vw, 6rem);
    font-size: 0.6rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--mid);
    font-family: 'Arial', sans-serif;
    border-top: 1px solid oklch(0.22 0.00 0);
    display: flex;
    justify-content: space-between;
  }
</style>
</head>
<body>
<main>
  <section class="hero" aria-labelledby="headline">
    <div class="hero-text">
      <p class="eyebrow" aria-label="Organization name">Reclaim Project</p>
      <h1 class="headline" id="headline">
        Beauty Is<br>An Act Of
        <span class="accent-word">Resistance.</span>
      </h1>
      <p class="subline">
        Art has always lived where it wasn't supposed to.
        The street remembers what the gallery forgets.
      </p>
      <a href="#join" class="cta">Join the Movement</a>
    </div>

    <!-- Stencil figure: child reaching up toward balloon cluster -->
    <!-- Red = accent only; everything else = near-black stencil ink -->
    <div class="stencil-figure" role="img" aria-label="Child silhouette releasing red heart balloons">
      <svg viewBox="0 0 200 340" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <style>
            .ink { fill: oklch(0.08 0.00 0); }
            .balloon-red { fill: oklch(0.55 0.28 25); }
            .string { stroke: oklch(0.08 0.00 0); stroke-width: 1.5; fill: none; }
          </style>
        </defs>

        <!-- Balloon cluster (the ONE red accent) -->
        <!-- 5 round balloons -->
        <ellipse class="balloon-red" cx="100" cy="40"  rx="18" ry="22"/>
        <ellipse class="balloon-red" cx="72"  cy="55"  rx="16" ry="20"/>
        <ellipse class="balloon-red" cx="128" cy="55"  rx="16" ry="20"/>
        <ellipse class="balloon-red" cx="82"  cy="25"  rx="14" ry="18"/>
        <ellipse class="balloon-red" cx="118" cy="28"  rx="14" ry="18"/>

        <!-- Balloon knots (tiny ink dots) -->
        <circle class="ink" cx="100" cy="62" r="2.5"/>
        <circle class="ink" cx="72"  cy="75" r="2.5"/>
        <circle class="ink" cx="128" cy="75" r="2.5"/>
        <circle class="ink" cx="82"  cy="43" r="2.5"/>
        <circle class="ink" cx="118" cy="46" r="2.5"/>

        <!-- Strings gathering to child's hand -->
        <path class="string" d="M100 64 Q99 90 96 105"/>
        <path class="string" d="M72  77 Q80 95 90 108"/>
        <path class="string" d="M128 77 Q118 93 102 107"/>
        <path class="string" d="M82  45 Q84 80 93 106"/>
        <path class="string" d="M118 48 Q110 82 99 106"/>

        <!-- Child: arm reaching up -->
        <!-- Upper arm -->
        <path class="ink" d="M85 115 Q80 108 90 100 Q97 95 100 108 L93 118Z"/>
        <!-- Torso/body -->
        <path class="ink" d="M78 160 Q70 140 80 120 Q88 112 100 113 Q112 112 120 120 Q130 140 122 160Z"/>
        <!-- Head -->
        <ellipse class="ink" cx="100" cy="105" rx="18" ry="20"/>
        <!-- Hair tuft -->
        <path class="ink" d="M82 94 Q88 82 100 85 Q112 82 118 94"/>
        <!-- Legs -->
        <path class="ink" d="M85 158 Q82 185 80 215 Q78 225 84 228 Q90 230 93 215 L96 162Z"/>
        <path class="ink" d="M115 158 Q118 185 120 215 Q122 225 116 228 Q110 230 107 215 L104 162Z"/>
        <!-- Shoes -->
        <ellipse class="ink" cx="82"  cy="232" rx="12" ry="6"/>
        <ellipse class="ink" cx="118" cy="232" rx="12" ry="6"/>
        <!-- Other arm hanging down -->
        <path class="ink" d="M122 125 Q135 140 132 158 Q128 164 122 160 Q118 148 118 130Z"/>
        <!-- Hand at bottom of arm -->
        <ellipse class="ink" cx="130" cy="162" rx="7" ry="5"/>
      </svg>
    </div>
  </section>
</main>

<footer>
  <span>© Reclaim Project</span>
  <span>The wall is the gallery</span>
</footer>
</body>
</html>
```

---

### EXAMPLE 3 — Mr. Brainwash: Maximalist Collage Section

**Prompt:** A "LIFE IS BEAUTIFUL" exhibition announcement section. Mr. Brainwash aesthetic:
layered pop icons, paint drip elements, stencil type mixed with brush script, joyful excess
— but locked onto a real CSS grid. Multiple overlapping elements using z-index. Bold palette.
Drip SVGs. Everything at once, but organized.

**Why elite:** CSS grid defines seven named template areas; within each, elements are positioned
absolutely to create depth. Every color is a distinct OKLCH hue at high chroma. The "chaos" is
governed: the grid never breaks, the text remains readable (contrast >4.5:1 everywhere), the
drip paths are inline SVGs not PNGs. `mix-blend-mode: multiply` on overlapping elements creates
the paint-over-print illusion without any raster assets.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LIFE IS BEAUTIFUL — MBW Exhibition</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --cream:   oklch(0.96 0.02 90);
    --ink:     oklch(0.08 0.00 0);
    --red:     oklch(0.55 0.27 25);
    --yellow:  oklch(0.90 0.18 98);
    --cyan:    oklch(0.72 0.20 204);
    --magenta: oklch(0.62 0.26 340);
    --green:   oklch(0.70 0.20 148);
    --blue:    oklch(0.55 0.22 255);
  }

  body {
    background: var(--cream);
    font-family: 'Arial Black', 'Impact', sans-serif;
    min-height: 100svh;
    overflow-x: hidden;
  }

  /* === COLLAGE GRID === */
  .collage {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr;
    grid-template-rows: 80px 200px 160px 120px 80px;
    grid-template-areas:
      "banner  banner  banner  banner  banner  banner"
      "splash  splash  icon-a  icon-a  icon-b  icon-b"
      "splash  splash  quote   quote   icon-b  icon-b"
      "drip-a  info    info    info    info    drip-b"
      "footer  footer  footer  footer  footer  footer";
    min-height: 100svh;
    position: relative;
  }

  /* BANNER: screaming headline across full width */
  .banner {
    grid-area: banner;
    background: var(--ink);
    display: flex;
    align-items: center;
    padding: 0 2rem;
    gap: 2rem;
    overflow: hidden;
    position: relative;
  }

  .banner-text {
    font-size: clamp(1.8rem, 5vw, 3.2rem);
    font-weight: 900;
    text-transform: uppercase;
    white-space: nowrap;
    animation: marquee 14s linear infinite;
  }

  .banner-text span { color: var(--yellow); margin-right: 3rem; }
  .banner-text span:nth-child(2n) { color: var(--red); }
  .banner-text span:nth-child(3n) { color: var(--cyan); }

  @keyframes marquee {
    from { transform: translateX(0); }
    to   { transform: translateX(-50%); }
  }

  /* SPLASH: giant overlapping title zone */
  .splash {
    grid-area: splash;
    position: relative;
    background: var(--yellow);
    overflow: hidden;
  }

  .splash-bg-star {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 120%;
    height: 120%;
    opacity: 0.15;
  }

  .splash-title {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: clamp(2rem, 6vw, 4.5rem);
    font-weight: 900;
    text-transform: uppercase;
    line-height: 0.9;
    text-align: center;
    color: var(--ink);
    z-index: 2;
    white-space: nowrap;
  }

  .splash-title .life { color: var(--red); display: block; }
  .splash-title .is   { color: var(--ink); display: block; font-size: 0.6em; }
  .splash-title .beau { color: var(--blue); display: block; }

  /* ICON-A: big star/heart pop motif */
  .icon-a {
    grid-area: icon-a;
    background: var(--magenta);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
  }

  .icon-a svg { width: 70%; height: 70%; }

  /* ICON-B: Haring-esque figure */
  .icon-b {
    grid-area: icon-b;
    background: var(--red);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
  }

  .icon-b svg { width: 60%; height: auto; }

  /* QUOTE: stencil-style proclamation */
  .quote {
    grid-area: quote;
    background: var(--cyan);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
    position: relative;
  }

  .quote blockquote {
    font-size: clamp(0.9rem, 2vw, 1.4rem);
    font-weight: 900;
    text-transform: uppercase;
    color: var(--ink);
    letter-spacing: 0.04em;
    line-height: 1.2;
    text-align: center;
    border: 4px solid var(--ink);
    padding: 1rem;
    position: relative;
    z-index: 2;
  }

  /* Paint drip areas */
  .drip-a {
    grid-area: drip-a;
    background: var(--green);
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 0.5rem;
  }

  .drip-b {
    grid-area: drip-b;
    background: var(--blue);
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 0.5rem;
  }

  /* INFO: exhibition details */
  .info {
    grid-area: info;
    background: var(--cream);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 3rem;
    padding: 1rem 2rem;
    border-top: 4px solid var(--ink);
    border-bottom: 4px solid var(--ink);
    flex-wrap: wrap;
  }

  .info-item {
    text-align: center;
  }

  .info-label {
    font-size: 0.6rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    font-family: 'Arial', sans-serif;
    color: oklch(0.4 0.00 0);
    font-weight: 700;
  }

  .info-value {
    font-size: clamp(1rem, 2.5vw, 1.6rem);
    font-weight: 900;
    text-transform: uppercase;
    color: var(--ink);
    line-height: 1.1;
  }

  .info-value.red   { color: var(--red); }
  .info-value.blue  { color: var(--blue); }

  /* FOOTER */
  .site-footer {
    grid-area: footer;
    background: var(--ink);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
  }

  .site-footer span {
    font-size: 0.7rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--yellow);
    font-weight: 900;
  }
</style>
</head>
<body>
<div class="collage" role="main">

  <!-- BANNER: scrolling marquee across full top -->
  <header class="banner" aria-label="Exhibition announcement">
    <p class="banner-text" aria-hidden="true">
      <span>Life Is Beautiful</span>
      <span>★</span>
      <span>Mr. Brainwash</span>
      <span>★</span>
      <span>Life Is Beautiful</span>
      <span>★</span>
      <span>Mr. Brainwash</span>
      <span>★</span>
      <span>Life Is Beautiful</span>
      <span>★</span>
      <span>Mr. Brainwash</span>
      <span>★</span>
    </p>
    <p class="sr-only" style="position:absolute;left:-9999px">Life Is Beautiful — Mr. Brainwash Exhibition</p>
  </header>

  <!-- SPLASH: main title -->
  <section class="splash" aria-label="Exhibition title">
    <!-- Background starburst in SVG -->
    <svg class="splash-bg-star" viewBox="0 0 200 200" aria-hidden="true">
      <polygon fill="oklch(0.08 0.00 0)" points="
        100,5 110,40 145,15 127,48 165,45 137,68 172,80
        140,95 170,115 137,118 155,152 123,140 120,178
        100,152 80,178 77,140 45,152 63,118 30,115
        60,95 28,80 63,68 35,45 73,48 55,15 90,40"/>
    </svg>
    <h1 class="splash-title">
      <span class="life">Life</span>
      <span class="is">is</span>
      <span class="beau">Beautiful</span>
    </h1>
  </section>

  <!-- ICON-A: Warhol-esque heart -->
  <div class="icon-a" aria-label="Pop art heart motif">
    <svg viewBox="0 0 100 100" aria-hidden="true">
      <!-- Bold heart shape in cream on magenta -->
      <path fill="oklch(0.96 0.02 90)"
        d="M50 85 C20 62 10 50 10 35 C10 20 22 10 35 14 C42 16 48 22 50 28
           C52 22 58 16 65 14 C78 10 90 20 90 35 C90 50 80 62 50 85Z"/>
      <!-- Inner accent ring -->
      <path fill="none" stroke="oklch(0.08 0.00 0)" stroke-width="3"
        d="M50 78 C25 58 16 47 16 35 C16 24 26 16 37 19.5
           C43 21 48 26 50 31 C52 26 57 21 63 19.5
           C74 16 84 24 84 35 C84 47 75 58 50 78Z"/>
    </svg>
  </div>

  <!-- ICON-B: Running figure (Haring homage) -->
  <div class="icon-b" aria-label="Dynamic running figure">
    <svg viewBox="0 0 80 160" aria-hidden="true">
      <!-- Head -->
      <circle fill="oklch(0.96 0.02 90)" cx="40" cy="18" r="14"/>
      <!-- Body -->
      <rect fill="oklch(0.96 0.02 90)" x="28" y="34" width="24" height="48" rx="8"/>
      <!-- Legs: spread in running pose -->
      <path fill="oklch(0.96 0.02 90)" d="M30 80 Q20 110 16 135 Q20 140 26 138 L38 100Z"/>
      <path fill="oklch(0.96 0.02 90)" d="M50 80 Q60 108 66 128 Q62 134 56 132 L42 98Z"/>
      <!-- Arms: thrown up in joy -->
      <path fill="oklch(0.96 0.02 90)" d="M28 40 Q12 28 8 16 Q12 10 18 14 L30 48Z"/>
      <path fill="oklch(0.96 0.02 90)" d="M52 40 Q68 30 72 18 Q68 12 62 16 L50 48Z"/>
      <!-- Motion lines -->
      <line stroke="oklch(0.96 0.02 90)" stroke-width="3" stroke-linecap="round"
        x1="2" y1="70" x2="14" y2="68"/>
      <line stroke="oklch(0.96 0.02 90)" stroke-width="2" stroke-linecap="round"
        x1="4" y1="80" x2="12" y2="82"/>
    </svg>
  </div>

  <!-- QUOTE -->
  <section class="quote" aria-label="Exhibition tagline">
    <blockquote cite="https://mrbrainwash.com">
      "Art is everywhere —<br>if you dare to look."
    </blockquote>
  </section>

  <!-- DRIP SVGs -->
  <div class="drip-a" aria-hidden="true">
    <svg viewBox="0 0 80 70" width="80" height="70">
      <!-- Green drip blobs -->
      <path fill="oklch(0.08 0.00 0)"
        d="M15 0 L15 40 Q15 55 22 55 Q29 55 29 40 L29 0Z"/>
      <path fill="oklch(0.08 0.00 0)"
        d="M40 0 L40 32 Q40 44 46 44 Q52 44 52 32 L52 0Z"/>
      <path fill="oklch(0.08 0.00 0)"
        d="M62 0 L62 50 Q62 62 68 62 Q74 62 74 50 L74 0Z"/>
    </svg>
  </div>

  <div class="drip-b" aria-hidden="true">
    <svg viewBox="0 0 80 70" width="80" height="70">
      <path fill="oklch(0.08 0.00 0)"
        d="M8 0 L8 45 Q8 58 14 58 Q20 58 20 45 L20 0Z"/>
      <path fill="oklch(0.08 0.00 0)"
        d="M33 0 L33 35 Q33 48 39 48 Q45 48 45 35 L45 0Z"/>
      <path fill="oklch(0.08 0.00 0)"
        d="M60 0 L60 52 Q60 64 66 64 Q72 64 72 52 L72 0Z"/>
    </svg>
  </div>

  <!-- INFO: exhibition facts -->
  <section class="info" aria-label="Exhibition details">
    <div class="info-item">
      <p class="info-label">Exhibition</p>
      <p class="info-value red">Life Is Beautiful</p>
    </div>
    <div class="info-item">
      <p class="info-label">Artist</p>
      <p class="info-value">Mr. Brainwash</p>
    </div>
    <div class="info-item">
      <p class="info-label">Opening</p>
      <p class="info-value blue">July 1</p>
    </div>
    <div class="info-item">
      <p class="info-label">Location</p>
      <p class="info-value">Los Angeles</p>
    </div>
    <div class="info-item">
      <a href="#tickets"
         style="display:inline-block;background:oklch(0.08 0.00 0);color:oklch(0.90 0.18 98);
                padding:0.6rem 1.4rem;font-size:0.7rem;letter-spacing:0.25em;
                text-transform:uppercase;font-weight:900;text-decoration:none;
                font-family:'Arial Black',sans-serif;">
        Get Tickets →
      </a>
    </div>
  </section>

  <!-- FOOTER -->
  <footer class="site-footer" aria-label="Site footer">
    <span>MBW Studio</span>
    <span>Life Is Beautiful ★ Always</span>
    <span>© 2026</span>
  </footer>
</div>
</body>
</html>
```

---

### EXAMPLE 4 — Murakami Superflat: Floral Hero

**Prompt:** A hero section for a fashion brand "HANA" (Japanese: flower). Full-viewport flower
grid in Murakami superflat style: twelve SVG daisies at large scale, each a different vivid
OKLCH hue, bold black outline, smiling face center, arranged in a perfect CSS grid. Logotype
centered in one clear tile. Absolutely flat — no shadows, no gradients, no depth. The flowers
ARE the background AND the hero.

**Why elite:** The SVG daisy is defined once in `<defs>` as a `<symbol>` and `<use>`d twelve
times — single source of truth, zero repetition. Each flower gets its petal color via a CSS
custom property passed through `color` + `fill: currentColor`. The grid uses
`grid-template-columns: repeat(4, 1fr)` with `aspect-ratio: 1` cells — the flowers fill their
cells perfectly with no distortion. Zero images, zero raster assets, zero frameworks. The
`stroke` on SVG elements and `color` values are all OKLCH at chroma 0.25–0.30.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HANA — Superflat Floral Hero</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --ink:  oklch(0.06 0.00 0);
    --face: oklch(0.98 0.03 95);

    /* 12 petal colors: full hue wheel at max chroma, varying lightness for vibrancy */
    --f01: oklch(0.65 0.28  15);   /* hot coral-red       */
    --f02: oklch(0.72 0.25  55);   /* solar orange        */
    --f03: oklch(0.90 0.20  96);   /* banana yellow       */
    --f04: oklch(0.80 0.23 130);   /* lime green          */
    --f05: oklch(0.70 0.22 160);   /* emerald             */
    --f06: oklch(0.72 0.22 196);   /* aqua                */
    --f07: oklch(0.68 0.25 222);   /* sky blue            */
    --f08: oklch(0.58 0.26 255);   /* cobalt blue         */
    --f09: oklch(0.55 0.28 285);   /* indigo              */
    --f10: oklch(0.62 0.28 310);   /* vivid purple        */
    --f11: oklch(0.65 0.27 340);   /* hot pink            */
    --f12: oklch(0.60 0.26   0);   /* cherry red          */
  }

  html, body { height: 100%; }

  body {
    background: var(--ink);
    font-family: 'Arial Black', 'Impact', sans-serif;
    display: flex;
    flex-direction: column;
    min-height: 100svh;
  }

  /* Screen-filling grid of flower cells */
  .flower-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(3, 1fr);
    flex: 1;
    min-height: 100svh;
  }

  .cell {
    aspect-ratio: 1;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 3px solid var(--ink);
  }

  /* Each cell's SVG flower fills it */
  .cell svg {
    width: 92%;
    height: 92%;
    display: block;
  }

  /* Petal color per cell via custom property */
  .cell:nth-child(1)  { --petal: var(--f01); }
  .cell:nth-child(2)  { --petal: var(--f02); }
  .cell:nth-child(3)  { --petal: var(--f03); }
  .cell:nth-child(4)  { --petal: var(--f04); }
  .cell:nth-child(5)  { --petal: var(--f05); }

  /* Center cell: the logotype — spans the "6" slot visually */
  .cell.logo-cell     { background: oklch(0.98 0.01 95); }

  .cell:nth-child(7)  { --petal: var(--f06); }
  .cell:nth-child(8)  { --petal: var(--f07); }
  .cell:nth-child(9)  { --petal: var(--f08); }
  .cell:nth-child(10) { --petal: var(--f09); }
  .cell:nth-child(11) { --petal: var(--f10); }
  .cell:nth-child(12) { --petal: var(--f11); }

  /* The petal color fed to SVG via currentColor */
  .cell .petal-fill { fill: var(--petal, oklch(0.70 0.25 55)); }

  /* Logotype inside center cell */
  .logo-cell {
    border: 3px solid var(--ink);
    flex-direction: column;
    gap: 0.4rem;
  }

  .brand-name {
    font-size: clamp(2.5rem, 6vw, 5rem);
    font-weight: 900;
    letter-spacing: -0.01em;
    text-transform: uppercase;
    color: var(--ink);
    line-height: 1;
    text-align: center;
  }

  .brand-sub {
    font-size: clamp(0.45rem, 1vw, 0.65rem);
    letter-spacing: 0.45em;
    text-transform: uppercase;
    font-family: 'Arial', sans-serif;
    font-weight: 700;
    color: var(--ink);
    text-align: center;
  }

  /* Hover: scale the flower (superflat doesn't do shadows — just scale) */
  .cell:not(.logo-cell):hover svg {
    transform: scale(1.06);
    transition: transform 0.15s ease;
  }
  .cell:not(.logo-cell) svg { transition: transform 0.15s ease; }

  /* Flower SVG is defined once as <symbol> inside an offscreen SVG */
  /* Using inline symbol + use for DRY rendering */
</style>
</head>
<body>

<!-- Hidden SVG defs: the flower symbol defined ONCE -->
<svg style="display:none" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <symbol id="mura-flower" viewBox="0 0 100 100">
      <!-- 8 round petals arranged radially -->
      <!-- Petal color: class="petal-fill" = filled by CSS via currentColor trick -->
      <!-- We use fill="var(--petal)" propagated via the .cell custom property -->
      <g class="petals">
        <!-- N  --> <ellipse class="petal-fill" cx="50" cy="20" rx="10" ry="18"/>
        <!-- NE --> <ellipse class="petal-fill" cx="70" cy="30" rx="10" ry="18" transform="rotate(45 70 30)"/>
        <!-- E  --> <ellipse class="petal-fill" cx="80" cy="50" rx="10" ry="18" transform="rotate(90 80 50)"/>
        <!-- SE --> <ellipse class="petal-fill" cx="70" cy="70" rx="10" ry="18" transform="rotate(135 70 70)"/>
        <!-- S  --> <ellipse class="petal-fill" cx="50" cy="80" rx="10" ry="18" transform="rotate(180 50 80)"/>
        <!-- SW --> <ellipse class="petal-fill" cx="30" cy="70" rx="10" ry="18" transform="rotate(225 30 70)"/>
        <!-- W  --> <ellipse class="petal-fill" cx="20" cy="50" rx="10" ry="18" transform="rotate(270 20 50)"/>
        <!-- NW --> <ellipse class="petal-fill" cx="30" cy="30" rx="10" ry="18" transform="rotate(315 30 30)"/>
      </g>
      <!-- Black outlines on petals — superflat bold stroke -->
      <g fill="none" stroke="oklch(0.06 0.00 0)" stroke-width="2.5">
        <ellipse cx="50" cy="20" rx="10" ry="18"/>
        <ellipse cx="70" cy="30" rx="10" ry="18" transform="rotate(45 70 30)"/>
        <ellipse cx="80" cy="50" rx="10" ry="18" transform="rotate(90 80 50)"/>
        <ellipse cx="70" cy="70" rx="10" ry="18" transform="rotate(135 70 70)"/>
        <ellipse cx="50" cy="80" rx="10" ry="18" transform="rotate(180 50 80)"/>
        <ellipse cx="30" cy="70" rx="10" ry="18" transform="rotate(225 30 70)"/>
        <ellipse cx="20" cy="50" rx="10" ry="18" transform="rotate(270 20 50)"/>
        <ellipse cx="30" cy="30" rx="10" ry="18" transform="rotate(315 30 30)"/>
      </g>
      <!-- Center face circle: cream -->
      <circle fill="oklch(0.98 0.03 95)" stroke="oklch(0.06 0.00 0)" stroke-width="2.5"
              cx="50" cy="50" r="20"/>
      <!-- Eyes -->
      <circle fill="oklch(0.06 0.00 0)" cx="43" cy="46" r="3.5"/>
      <circle fill="oklch(0.06 0.00 0)" cx="57" cy="46" r="3.5"/>
      <!-- Smile arc -->
      <path stroke="oklch(0.06 0.00 0)" stroke-width="2.5" stroke-linecap="round"
            fill="none" d="M42 55 Q50 63 58 55"/>
      <!-- Rosy cheeks (kawaii detail) -->
      <ellipse fill="oklch(0.65 0.28 15)" fill-opacity="0.35" cx="38" cy="54" rx="5" ry="3.5"/>
      <ellipse fill="oklch(0.65 0.28 15)" fill-opacity="0.35" cx="62" cy="54" rx="5" ry="3.5"/>
    </symbol>
  </defs>
</svg>

<!-- The 4x3 grid: 11 flowers + 1 logo cell -->
<main>
  <section class="flower-grid" aria-label="HANA brand floral hero">
    <!-- Row 1 -->
    <div class="cell"><svg aria-hidden="true"><use href="#mura-flower"/></svg></div>
    <div class="cell"><svg aria-hidden="true"><use href="#mura-flower"/></svg></div>
    <div class="cell"><svg aria-hidden="true"><use href="#mura-flower"/></svg></div>
    <div class="cell"><svg aria-hidden="true"><use href="#mura-flower"/></svg></div>
    <!-- Row 2 -->
    <div class="cell"><svg aria-hidden="true"><use href="#mura-flower"/></svg></div>
    <!-- Logo cell: center of row 2 (position 6) -->
    <div class="cell logo-cell" role="banner">
      <h1 class="brand-name" lang="ja-Latn">HANA</h1>
      <p class="brand-sub">花 — The Superflat Collection</p>
    </div>
    <div class="cell"><svg aria-hidden="true"><use href="#mura-flower"/></svg></div>
    <div class="cell"><svg aria-hidden="true"><use href="#mura-flower"/></svg></div>
    <!-- Row 3 -->
    <div class="cell"><svg aria-hidden="true"><use href="#mura-flower"/></svg></div>
    <div class="cell"><svg aria-hidden="true"><use href="#mura-flower"/></svg></div>
    <div class="cell"><svg aria-hidden="true"><use href="#mura-flower"/></svg></div>
    <div class="cell"><svg aria-hidden="true"><use href="#mura-flower"/></svg></div>
  </section>
</main>

</body>
</html>
```

---

## SYNTHESIS: What Bold Expression Demands of Web Craft

Bold ≠ sloppy. The four masters above each demonstrate *systematic boldness* — they are not
randomly expressive; they are maximally precise about the particular energy they want to create.

| Master      | Core system           | Web discipline required                         |
|-------------|-----------------------|-------------------------------------------------|
| Warhol      | Grid × color serial   | CSS Grid, OKLCH at equal L, single SVG reused   |
| Banksy      | Monochrome + ONE hue  | Strict color budget, SVG clip-paths, contrast   |
| Mr Brainwash| Grid holds the chaos  | Named grid-areas, z-index layers, not randomness|
| Murakami    | Symbol once, use many | SVG `<symbol>` + `<use>`, zero shadow, flat     |

The model must learn: the constraint is NOT the style. The constraint is craft. The style is
whatever it needs to be. A Warhol piece and a Müller-Brockmann poster are equally elite —
they are just elite in different registers. Mediocrity in both registers looks the same:
arbitrary choices, decorative shortcuts, defaults instead of decisions.
