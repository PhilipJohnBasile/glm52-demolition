#!/usr/bin/env python3
"""Design render + critique loop — the visual equivalent of "run the tests".

The model generates HTML/CSS, we RENDER it headless (Playwright), MEASURE objective
design facts (WCAG contrast, type scale consistency, palette, framework-default
tells), feed those measurements back, and the model critiques + revises. Because
GLM-5.2 is text-only, we don't ask it to "look" — we give it measured facts it can
act on, plus save a screenshot for you.

  pip install playwright && python -m playwright install chromium
  python scripts/25_design_critique.py --base-url http://localhost:8081/v1 \
      --task "a pricing page hero, art-directed, not a framework template"

Loops generate -> measure -> revise up to --rounds, returns the best HTML + a report.
"""

import argparse
import json
import os
import re
import sys
import urllib.request

SYS = ("You are a senior designer. Output a SINGLE self-contained HTML document "
       "with inline <style>. Use a bespoke OKLCH token system, a modular type "
       "scale, CSS Grid composition, and one signature move. Do NOT use Tailwind/"
       "Bootstrap or generic 'rounded card + shadow' defaults. Output ONLY the HTML.")


def chat(base_url, messages):
    body = json.dumps({"model": "local", "messages": messages,
                       "temperature": 0.4, "max_tokens": 2600}).encode()
    req = urllib.request.Request(base_url + "/chat/completions", body,
                                 {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]["content"]


def extract_html(t):
    m = re.search(r"```html\n(.*?)```", t, re.S) or re.search(r"(<!DOCTYPE.*?</html>)", t, re.S)
    return m.group(1) if m else t


def _lum(rgb):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2])


def contrast(fg, bg):
    a, b = _lum(fg), _lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def measure(html, shot_path):
    """Render headless, return measured design facts (+ save screenshot)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": 1280, "height": 900})
        pg.set_content(html, wait_until="networkidle")
        pg.screenshot(path=shot_path, full_page=True)
        data = pg.evaluate(r"""() => {
          const out={texts:[], fontSizes:new Set(), colors:new Set()};
          for (const el of document.querySelectorAll('h1,h2,h3,p,a,button,span,li')){
            const s=getComputedStyle(el); const t=(el.textContent||'').trim();
            if(!t) continue;
            out.fontSizes.add(parseFloat(s.fontSize));
            out.colors.add(s.color);
            // walk up for an opaque background
            let bg=s.backgroundColor, n=el;
            while((bg==='rgba(0, 0, 0, 0)'||bg==='transparent') && n.parentElement){n=n.parentElement; bg=getComputedStyle(n).backgroundColor;}
            out.texts.push({fg:s.color, bg, size:parseFloat(s.fontSize), weight:s.fontWeight});
          }
          out.fontSizes=[...out.fontSizes]; out.colors=[...out.colors];
          return out;
        }""")
        br.close()
    return data


def parse_rgb(s):
    m = re.findall(r"[\d.]+", s)
    return [float(m[0]), float(m[1]), float(m[2])] if len(m) >= 3 else [0, 0, 0]


def critique(html, m):
    """Turn measurements into objective design findings."""
    issues = []
    # WCAG contrast
    fails = 0
    for t in m["texts"]:
        c = contrast(parse_rgb(t["fg"]), parse_rgb(t["bg"]))
        large = t["size"] >= 24 or (t["size"] >= 18.66 and int(float(t["weight"] or 400)) >= 700)
        if c < (3 if large else 4.5):
            fails += 1
    if fails:
        issues.append(f"{fails} text elements FAIL WCAG contrast (4.5:1 / 3:1 large).")
    # type scale
    if len(m["fontSizes"]) > 6:
        issues.append(f"{len(m['fontSizes'])} distinct font sizes — not on a tight modular scale.")
    # OKLCH usage (cookie-cutter tell: rgb/hex only)
    if not re.search(r"oklch|oklab", html, re.I):
        issues.append("No OKLCH/OKLab — using rgb/hex; switch to a perceptual OKLCH ramp.")
    # framework-default tells
    if re.search(r"\b(rounded-lg|shadow-md|bg-gray-|btn-primary|container mx-auto)\b", html):
        issues.append("Framework-default utility classes detected — make it bespoke.")
    if "grid-template" not in html and "display:grid" not in html.replace(" ", ""):
        issues.append("No CSS Grid composition — layout likely generic.")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8081/v1")
    ap.add_argument("--task", required=True)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--out", default="design_out")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    msgs = [{"role": "system", "content": SYS},
            {"role": "user", "content": f"Design: {args.task}"}]
    html, best = "", None
    for r in range(args.rounds):
        html = extract_html(chat(args.base_url, msgs))
        path = os.path.join(args.out, f"round{r}.html")
        open(path, "w").write(html)
        try:
            m = measure(html, os.path.join(args.out, f"round{r}.png"))
            issues = critique(html, m)
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] render/measure failed ({e}); install playwright?")
            issues = []
        print(f"=== round {r}: {len(issues)} findings ===")
        for i in issues:
            print("  -", i)
        if not issues:
            best = html
            break
        best = html
        msgs += [{"role": "assistant", "content": f"```html\n{html}\n```"},
                 {"role": "user", "content": "Measured findings:\n- " +
                  "\n- ".join(issues) + "\nFix every one and return the revised HTML."}]
    open(os.path.join(args.out, "final.html"), "w").write(best or html)
    print(f"\n>> final design -> {args.out}/final.html (+ round screenshots)")


if __name__ == "__main__":
    main()
