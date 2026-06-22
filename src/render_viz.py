"""Render-based visual generation — the QUALITY-FIRST 'image gen' for MATH / ARCHITECTURE /
DATA. Diffusion can't draw an exact equation, a correct chart, or real UML; CODE can —
precise, reproducible, VERIFIABLE, zero quality variance. Render to PNG, then SEE it
(vision.py) to close the loop.
  matplotlib/numpy -> math & data plots      mermaid/graphviz -> architecture & flow
  tikz -> publication figures                manim -> math ANIMATION (video)
"""
import os
import shutil
import subprocess
import tempfile


def render_viz(spec, kind="matplotlib", out="/tmp/viz.png"):
    """spec -> PNG (manim -> mp4). kind: matplotlib | mermaid | graphviz/dot | tikz | manim."""
    kind = (kind or "matplotlib").lower()
    try:
        if kind in ("matplotlib", "mpl", "plot"):
            return _mpl(spec, out)
        if kind == "mermaid":
            return _cli("mmdc", ["mmdc", "-i", "{in}", "-o", out, "-s", "2"], spec, ".mmd", out,
                        "npm i -g @mermaid-js/mermaid-cli")
        if kind in ("graphviz", "dot"):
            return _cli("dot", ["dot", "-Tpng", "-Gdpi=140", "-o", out, "{in}"], spec, ".dot", out,
                        "brew install graphviz")
        if kind == "tikz":
            return _tikz(spec, out)
        if kind == "manim":
            return _manim(spec, out)
        return f"unknown kind {kind!r} (matplotlib/mermaid/graphviz/tikz/manim)"
    except Exception as e:  # noqa: BLE001
        return f"render error ({kind}): {str(e)[:200]}"


def _mpl(code, out):
    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    import matplotlib.pyplot as plt
    g = {"plt": plt, "np": np, "numpy": np, "__name__": "__viz__"}
    exec(code, g)                                           # plotting code using plt / np
    plt.savefig(out, dpi=140, bbox_inches="tight")
    plt.close("all")
    return out if os.path.exists(out) else "no figure produced (call plt.plot/…)"


def _cli(binname, cmd, spec, ext, out, hint):
    if not shutil.which(binname):
        return f"{binname} not installed ({hint}) — spec is valid; renders once installed"
    with tempfile.NamedTemporaryFile("w", suffix=ext, delete=False) as f:
        f.write(spec)
        src = f.name
    subprocess.run([c.replace("{in}", src) for c in cmd], capture_output=True, timeout=90)
    return out if os.path.exists(out) else "render failed (check the spec)"


def _tikz(spec, out):
    if not shutil.which("pdflatex"):
        return "pdflatex not installed (brew install --cask mactex-no-gui); spec valid"
    doc = ("\\documentclass[tikz,border=4pt]{standalone}\n\\begin{document}\n"
           + spec + "\n\\end{document}")
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "t.tex"), "w").write(doc)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "t.tex"], cwd=d,
                       capture_output=True, timeout=90)
        pdf = os.path.join(d, "t.pdf")
        if os.path.exists(pdf) and shutil.which("magick"):
            subprocess.run(["magick", "-density", "150", pdf, out], capture_output=True, timeout=60)
        return out if os.path.exists(out) else "tikz->pdf ok (need imagemagick to rasterize)"


def _manim(spec, out):
    if not shutil.which("manim"):
        return "manim not installed (uv pip install manim) — math ANIMATION; spec valid"
    mp4 = out.rsplit(".", 1)[0] + ".mp4"
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "s.py"), "w").write(spec)
        subprocess.run(["manim", "-qm", os.path.join(d, "s.py")], cwd=d,
                       capture_output=True, timeout=300)
        for root, _, files in os.walk(d):
            for f in files:
                if f.endswith(".mp4"):
                    shutil.copy(os.path.join(root, f), mp4)
                    return mp4
        return "manim render failed (check the Scene)"


def critique(image_path, criteria="Is this figure clear, correct, and well-labeled? List issues."):
    """Close the loop — the VLM JUDGES the rendered figure (quality, not just that it exists)."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from vision import see
    return see(image_path, criteria)


def selftest():
    out = render_viz("import numpy as np\nx=np.linspace(0,6.283,200)\n"
                     "plt.plot(x,np.sin(x)); plt.title('sin x'); plt.grid(True)",
                     "matplotlib", "/tmp/_viz_test.png")
    ok = isinstance(out, str) and out.endswith(".png") and os.path.exists(out)
    print(f"  render_viz selftest: matplotlib={ok} -> {out}  {'PASS ✅' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
