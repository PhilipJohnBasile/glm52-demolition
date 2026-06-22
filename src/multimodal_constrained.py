"""#42-44 — the CONSTRAINED layer for MLX multimodal: palette-steered best-of-N image gen (#42), schema-
structured vision reading (#43), verified manim/code video gen (#44). The generation backends already exist
(src/imagegen.py diffusion, src/vision.py mlx-vlm, src/render_viz.py manim); this adds the verify/select
layer (GPU-free logic + selftest) that makes their output CONSTRAINED — the verify-everything thesis applied
to pixels and frames. The live generation is the GPU/compute backend; the gates here are cheap + testable.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from constrained_decode import ColorValidator, ToolJSONValidator  # noqa: E402


def palette_best_of_n(candidates, target_hues, palette_of):
    """#42: from N generated images, pick the one whose palette is most HARMONIOUS with the target/brand hues
    (OKLCH harmony from ColorValidator). candidates: ids; palette_of(id)->list[hue]. Best-of-N + palette-steer
    so diffusion output lands on-brand instead of random."""
    cv = ColorValidator()

    def score(cand):
        hues = palette_of(cand)
        return sum(1 for h in hues for t in target_hues if cv.harmonious(h, t))

    return max(candidates, key=score) if candidates else None


def structured_vision(raw_text, required_keys):
    """#43: constrain a VLM's image/video description to a JSON object carrying the required keys (structured
    reading). Returns the parsed dict if valid + complete, else None so the agent retries/repairs."""
    block = re.search(r"\{.*\}", raw_text, re.S)
    if not block or not ToolJSONValidator.balanced(block.group(0)):
        return None
    try:
        obj = json.loads(block.group(0))
    except Exception:  # noqa: BLE001
        return None
    return obj if all(k in obj for k in required_keys) else None


def verified_manim(code):
    """#44: a video-gen candidate is valid manim only if it parses + honours the Scene.construct render
    contract. The real render (render_viz manim -> mp4) is the GPU/compute verify; this is the cheap gate."""
    try:
        compile(code, "<manim>", "exec")
    except SyntaxError:
        return False
    return "class" in code and "Scene" in code and "construct" in code


def _selftest():
    best = palette_best_of_n(["a", "b"], [150], {"a": [330, 150], "b": [200, 50]}.__getitem__)
    assert best == "a", best                                   # 'a' harmonizes (complement 330 + same 150)
    assert structured_vision('desc: {"objects": ["cat"], "scene": "indoor"}', ["objects", "scene"])
    assert structured_vision("no json here", ["objects"]) is None
    assert verified_manim("class S(Scene):\n    def construct(self):\n        pass")
    assert not verified_manim("class S(:\n  bad")
    print("  multimodal_constrained selftest PASS (#42-44): palette-best-of-N + structured-vision + verified-manim")


if __name__ == "__main__":
    _selftest()
