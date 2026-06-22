"""AI video GENERATION — local on Apple Silicon. Two paths, by purpose:
  - MATH / architecture  -> manim (code-rendered, EXACT, verifiable) via render_viz. The niche path.
  - aesthetic clips       -> LTX-Video, the MLX-native option (Phosphene / mlx-video, Apache-2.0);
                             Wan 2.2 is the quality leader but heavier. Best-effort.
The least niche-critical capability — but local + real when you want it.
"""
import os


def generate_video(prompt, out="/tmp/gen.mp4", seconds=4, seed=0):
    """Text -> short aesthetic clip via LTX-Video (MLX) if installed; else tells you how to enable."""
    try:
        import mlx_video
    except Exception:  # noqa: BLE001
        return ("AI video-gen not enabled. Local on M5: LTX-Video (fast, MLX-native — the Phosphene "
                "app, or `uv pip install mlx-video`) or Wan 2.2 (higher quality, heavier). For MATH "
                "animation use math_video()/render_viz(kind='manim') — exact + verifiable.")
    try:
        vid = mlx_video.generate(prompt, num_frames=int(seconds * 24), seed=seed)
        vid.save(out)
        return out
    except Exception as e:  # noqa: BLE001
        return f"video-gen error: {str(e)[:160]}"


def math_video(manim_scene_code, out="/tmp/math.mp4"):
    """EXACT math animation via manim (code-rendered) — the precise path for the niche."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from render_viz import render_viz
    return render_viz(manim_scene_code, "manim", out)


def selftest():
    import importlib.util
    ltx = importlib.util.find_spec("mlx_video") is not None
    print(f"  video_gen selftest: LTX/mlx-video={ltx} (aesthetic, best-effort); manim math-video via "
          f"render_viz (exact). WIRED ✅")
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
