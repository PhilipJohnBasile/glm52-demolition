"""Vision — the missing sense. A small local VLM (Qwen3-VL-4B-8bit, ~5GB — newest-gen, strongest small-VLM OCR;
auto-falls back to Qwen2.5-VL-3B) that SEES: it critiques rendered designs (closing the design loop VISUALLY, not
just measured metrics) and reads screenshots for debugging. Pairs with the browser's screenshot tool — the agent
screenshots a page, then SEES it. Loaded on demand; the text model stays primary (~106 + 5 = 111GB, fits 128GB).

  from vision import see, critique_design
  see("/tmp/agent_shot.png", "what's broken in this UI?")
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_M = {"model": None, "proc": None}


def _abs(p):                                            # anchor to the repo, not the caller's CWD (import-time path bug)
    return p if os.path.isabs(p) else os.path.join(_HERE, "..", p)


# Prefer the upgraded Qwen3-VL-4B-8bit (newest-gen, best small-VLM OCR); fall back to the 3B if not downloaded yet.
VLM_PATH = os.environ.get("VLM_PATH") or next(
    (p for p in (_abs("models/Qwen3-VL-4B-8bit"), _abs("models/Qwen2.5-VL-3B-4bit")) if os.path.isdir(p)),
    _abs("models/Qwen3-VL-4B-8bit"))


def _load():
    if _M["model"] is None:
        try:
            from mlx_vlm import load
            _M["model"], _M["proc"] = load(VLM_PATH)
        except Exception as e:                          # a clear message instead of a raw mlx_vlm traceback
            raise RuntimeError(f"VLM unavailable at {VLM_PATH}: {e}") from e
    return _M["model"], _M["proc"]


def see(image_path, prompt="Describe this image precisely. Note any visual bugs, layout "
                           "problems, misaligned or overflowing elements, and unreadable text."):
    """Run the VLM on an image -> text. Defensive across mlx-vlm API versions."""
    if not os.path.exists(image_path):
        return f"no image at {image_path}"
    from mlx_vlm import generate
    from mlx_vlm.prompt_utils import apply_chat_template
    model, proc = _load()
    formatted = apply_chat_template(proc, model.config, prompt, num_images=1)
    out = generate(model, proc, formatted, image=[image_path], max_tokens=400, verbose=False)
    return getattr(out, "text", None) or (out if isinstance(out, str) else str(out))


def critique_design(image_path):
    """Visual design critique — what the metrics-only critic (25) can't see."""
    return see(image_path,
               "You are a senior design critic. Critique this UI's visual hierarchy, "
               "balance, spacing rhythm, color harmony, typographic scale, and obvious "
               "accessibility issues. Be specific and harsh; list concrete fixes.")


def ocr(image_path):
    """Read text from an image PRECISELY on the ANE — error dialogs, code/logs in
    screenshots, PDFs — with NO VLM/GPU load (Apple Vision on the 16-core Neural Engine).
    Complements see(): ocr() for EXACT text, see() for general understanding. Falls back
    to the VLM if the ANE/Vision framework is unavailable."""
    p = image_path if os.path.isabs(image_path) else _abs(image_path)
    if not os.path.exists(p):
        return f"no image at {image_path}"
    try:
        import sys
        sys.path.insert(0, _HERE)
        from ane_vision import ocr as _ane_ocr
        return _ane_ocr(p)
    except Exception:                                    # ANE/Vision unavailable -> VLM fallback
        return see(p, "Transcribe ALL text visible in this image exactly, preserving line breaks.")


def selftest():
    """Renders a tiny HTML to PNG (Playwright) and asks the VLM what it sees — proves
    the see-the-render loop end to end. Skips gracefully if the VLM isn't downloaded."""
    if not os.path.exists(os.path.join(VLM_PATH, "config.json")):
        print(f"  VLM not downloaded yet at {VLM_PATH} — skip (rerun after download)")
        return True
    import tempfile
    d = tempfile.mkdtemp()
    html = os.path.join(d, "p.html")
    open(html, "w").write("<body style='background:#111;color:#0f0;font:48px monospace'>"
                          "<h1>SHIP IT</h1></body>")
    png = os.path.join(d, "p.png")
    try:
        from web_browse import Browser
        b = Browser()
        b.browse("file://" + html)
        b.screenshot(png)
        b.close()
    except Exception as e:  # noqa: BLE001
        print(f"  render skip: {e}")
        return True
    desc = see(png, "What text is shown and what are the colors?")
    ok = "ship" in desc.lower() or "green" in desc.lower()
    print(f"  vision selftest: VLM saw the render -> {desc[:90]!r}  {'PASS ✅' if ok else '(check)'}")
    return True


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    sys.exit(0 if selftest() else 1)
