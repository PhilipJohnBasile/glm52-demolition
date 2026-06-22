"""#17 Design-soul — make the model ELITE out of the box, not just competent.

The base model's prior is "competent" (the average of millions of hex-color/arbitrary-spacing pages); elite
specifics (OKLCH, 8px grid, modular type scale, WCAG) are rare in pretraining so it reverts to the mean. We
override the mean three ways:
  1. STEER  — `CANON` system prompt baked into design serving (this file). Immediate, no GPU.
  2. GUARANTEE — constrained_decode bans non-OKLCH tokens at generation (deterministic, can't miss).
  3. NATIVE — heal on verified-elite examples (#17 flywheel: generate→audit→keep-elite→SFT) so the PRIOR
     becomes elite and no constraint is needed.
`audit_design()` is the verifier that powers both the GUARANTEE gate and the heal's keep-only-elite filter.
Static + GPU-free; the render critic (verifiers.py) adds real rendered-WCAG on top.
"""
import re

# ── Layer 1: the canon (served as the default system prompt for design tasks) ───────────────────────
CANON = """You are an ELITE product designer. Every design obeys these non-negotiables — they separate competent from elite:

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

Output production-ready HTML+CSS with CSS custom properties for the OKLCH palette and the spacing scale."""

# ── the audit gate (verifies a design is elite; powers the constrain gate + the heal filter) ─────────
_BANNED_COLOR = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b|\brgba?\(|\bhsla?\(")
_SPACING_DECL = re.compile(r"(?:margin|padding|gap|row-gap|column-gap)[^:;{}]*:\s*([^;}]+)", re.I)  # spacing rhythm only — NOT absolute positioning (top/left are functional placement, not the 8px grid)
_PX = re.compile(r"(\d{1,7}(?:\.\d{1,4})?)px")               # bounded: stops ReDoS O(n²) backtracking on huge digit runs
_FONT_PX = re.compile(r"font-size\s*:\s*(\d{1,7}(?:\.\d{1,4})?)px", re.I)
_SCALE = {12.0, 16.0, 20.0, 25.0, 31.0, 39.0, 49.0, 61.0}        # 1.25 modular scale

# COOKIE-CUTTER detector — the user's core want: bespoke, not framework-default. Technically-elite OKLCH can
# still be generic Bootstrap/Tailwind garbage; reject the framework tells so the heal corpus is hand-crafted only.
_COOKIE_CUTTER = [
    (re.compile(r"bootstrap(?:\.min)?\.(?:css|js)|\bbtn-(?:primary|secondary|success|danger|info|warning)\b"
                r"|\bcol-(?:xs|sm|md|lg|xl)-\d+\b|\bnavbar-(?:brand|toggler|nav)\b|\bform-control\b|\binput-group\b"), "Bootstrap"),
    (re.compile(r"cdn\.tailwindcss|tailwind(?:\.min)?\.css"), "Tailwind-CDN"),
    (re.compile(r"\bMui[A-Z]\w+|@mui/|@chakra-ui|\bchakra-\w+|\bant-(?:btn|layout|menu|row|col)\b"), "component-lib (MUI/Chakra/Ant)"),
    (re.compile(r"\buseState\s*\(|\buseEffect\s*\(|import\s+React\b|className="), "React boilerplate"),
]
_UTIL = re.compile(r"\b(?:flex|grid|px-\d|py-\d|pt-\d|pb-\d|mx-\d|my-\d|text-(?:xs|sm|base|lg|xl|\d)|bg-\w+-\d+"
                   r"|rounded(?:-\w+)?|shadow(?:-\w+)?|gap-\d|w-\d|h-\d|items-\w+|justify-\w+)\b")


def cookie_cutter_tells(code: str):
    """Framework/cookie-cutter tells found (Bootstrap, Tailwind-soup, MUI/Chakra/Ant, React boilerplate). [] = bespoke."""
    tells = [name for rx, name in _COOKIE_CUTTER if rx.search(code)]
    if any(len(_UTIL.findall(m)) >= 5 for m in re.findall(r'class="([^"]+)"', code)):
        tells.append("Tailwind-utility-soup (≥5 utilities/class)")
    return tells


def _grid_ok(v: float) -> bool:
    return v in (0.0, 1.0, 2.0) or v % 4 == 0                     # 0/1/2 allow borders/hairlines


def audit_design(css: str):
    """Eliteness violations ([] = elite): OKLCH-only, 8px-grid, type-scale, AND bespoke (no cookie-cutter frameworks)."""
    css = re.sub(r"/\*.*?\*/|<!--.*?-->", "", css, flags=re.S)   # ignore comments: hex/framework names in comments aren't usage
    v = []
    bad = _BANNED_COLOR.findall(css)
    if bad:
        v.append(f"non-OKLCH color ({len(bad)}×, e.g. {bad[0]!r}) — use oklch()")
    off = sorted({float(px) for decl in _SPACING_DECL.findall(css) for px in _PX.findall(decl) if not _grid_ok(float(px))})
    if off:
        v.append(f"off-8px-grid spacing {off[:5]} — use multiples of 4")
    bad_type = sorted({float(s) for s in _FONT_PX.findall(css) if float(s) not in _SCALE})
    if bad_type:
        v.append(f"off-modular-scale font-size {bad_type[:5]} — use 12/16/20/25/31/39")
    cc = cookie_cutter_tells(css)
    if cc:
        v.append(f"cookie-cutter: {cc} — hand-write bespoke CSS, no frameworks")
    return v


def is_elite(css: str) -> bool:
    return not audit_design(css)


def _selftest():
    gold = (":root{--brand:oklch(0.62 0.19 255);--space:8px}\n"
            ".card{padding:16px;margin:24px 0;gap:8px;border:1px solid oklch(0.9 0.02 255);"
            "border-radius:8px;font-size:16px;color:oklch(0.2 0.02 255)}\n"
            "h1{font-size:31px;line-height:1.2}")
    bad = (".card{padding:13px;margin:5px;background:#ffffff;color:rgb(17,17,17);"
           "font-size:17px;gap:7px}")
    bootstrap = '<link href="bootstrap.min.css"><button class="btn btn-primary">Go</button><div class="col-md-6"></div>'
    tailwind = '<div class="flex items-center justify-center px-4 py-2 bg-blue-500 rounded-lg shadow-md gap-2">x</div>'
    gv, bv = audit_design(gold), audit_design(bad)
    boot, tw = cookie_cutter_tells(bootstrap), cookie_cutter_tells(tailwind)
    print(f"  GOLD (bespoke elite) → {len(gv)} violations {gv if gv else '✓'}")
    print(f"  BAD  (hex/off-grid)  → {len(bv)} violations:")
    for x in bv:
        print(f"      • {x}")
    print(f"  BOOTSTRAP            → cookie-cutter {boot}")
    print(f"  TAILWIND-soup        → cookie-cutter {tw}")
    assert gv == [], gv                                       # bespoke gold stays clean (no false-positive)
    assert len(bv) == 3, bv
    assert "Bootstrap" in boot and any("Tailwind" in t for t in tw), (boot, tw)
    assert audit_design("/* fallback #ffffff */ .x{color:oklch(0.2 0.02 250); padding:16px}") == [], "hex-in-comment false-positive"
    print("  design_canon selftest PASS — gates OKLCH/grid/scale + BESPOKE, comment-robust (hex/framework in comments ≠ usage)")


if __name__ == "__main__":
    _selftest()
