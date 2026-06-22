"""Image generation — QUALITY-first local design mockups + art. We have 128 GB, so we DON'T over-quantize:
run the *dev* tier at 8-bit. CLOSE THE LOOP: render -> SEE (vision.py) -> critique -> regenerate until it
passes the design soul. For EXACT math/architecture figures use render_viz.py (code-rendered), not diffusion.

Re-wired 2026-06-19 for the NEW mflux API (Flux1 relocated to mflux.models.flux.variants.txt2img.flux;
ModelConfig + Config removed; generate_image takes direct kwargs; img2img folded into generate_image via
image_path). GPU + weights test pending — the heal chain owns the GPU right now.

  generate_image("a minimal SaaS pricing hero, dark, OKLCH greens", model="dev")
  generate_and_critique(prompt, criteria="clean type scale, real contrast", tries=3)
"""
import os

_CACHE = {}
_STEPS = {"schnell": 4, "dev": 28}
_MODEL_PATH = {"dev": "dev", "schnell": "schnell"}          # mflux short names; swap to HF ids if needed


def _flux1(variant, bits):
    key = ("f1", variant, bits)
    if key not in _CACHE:
        from mflux.models.flux.variants.txt2img.flux import Flux1
        _CACHE[key] = Flux1(quantize=bits, model_path=_MODEL_PATH.get(variant, variant))
    return _CACHE[key]


def _flux2(variant, bits):
    """FLUX.2 (klein 9B / dev 32B) via an Apple-Silicon MLX port if installed. Best-effort."""
    try:
        import mlx_flux2
    except Exception:
        return None
    key = ("f2", variant, bits)
    if key not in _CACHE:
        _CACHE[key] = mlx_flux2.load(variant, quantize=bits)
    return _CACHE[key]


def generate_image(prompt, out_path="/tmp/agent_gen.png", model="dev", bits=8, steps=None, seed=0, size=1024):
    """Text -> image (PNG). model: dev|schnell (Flux.1) or flux2-* (if mlx-flux2). Returns the path."""
    m = (model or "dev").lower()
    if m.startswith("flux2"):
        variant = "dev" if "dev" in m else "klein"
        f2 = _flux2(variant, bits)
        if f2 is not None:
            try:
                img = f2.generate(prompt, steps=steps or (28 if variant == "dev" else 4),
                                  seed=seed, height=size, width=size)
                img.save(out_path)
                return out_path
            except Exception as e:
                return f"flux2 error: {str(e)[:140]}"
        m = "dev"
    variant = "dev" if "dev" in m else "schnell"
    try:
        flux = _flux1(variant, bits)
        img = flux.generate_image(seed=seed, prompt=prompt,
                                  num_inference_steps=steps or _STEPS[variant], height=size, width=size)
        img.save(out_path)
        return out_path
    except Exception as e:
        return f"imagegen error: {str(e)[:200]} (weights download ~on first use)"


def img2img(prompt, init_image, out_path="/tmp/agent_img2img.png", model="dev", bits=8,
            steps=None, seed=0, size=1024):
    """#101: Image-to-Image via the new mflux — generate_image with image_path (the separate img2img variant
    was folded into the main path). Returns the output path (or an error string)."""
    variant = "dev" if "dev" in (model or "dev").lower() else "schnell"
    try:
        flux = _flux1(variant, bits)
        img = flux.generate_image(seed=seed, prompt=prompt, num_inference_steps=steps or _STEPS[variant],
                                  height=size, width=size, image_path=init_image)
        img.save(out_path)
        return out_path
    except Exception as e:
        return f"img2img error: {str(e)[:200]}"


def generate_and_critique(prompt, out_path="/tmp/agent_gen.png",
                          criteria="clean type scale, real contrast, no AI artifacts, on-brand",
                          model="dev", tries=3):
    """QUALITY loop: generate -> the VLM critiques vs the design soul -> regenerate with the feedback."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from vision import see
    fb = ""
    for i in range(tries):
        p = generate_image(prompt + (f". Fix these: {fb}" if fb else ""), out_path, model=model, seed=i)
        if not isinstance(p, str) or not os.path.exists(p):
            return p
        verdict = see(p, f"Judge this against: {criteria}. Reply PASS if good, else list concrete fixes.")
        if "PASS" in verdict.upper():
            return f"{p} (passed critique in {i + 1} tries)"
        fb = verdict[:200]
    return f"{out_path} (best of {tries}; last critique: {fb[:120]})"


def selftest():
    """Verify the wiring matches the new mflux API (GPU-free — no weights download)."""
    try:
        import inspect
        from mflux.models.flux.variants.txt2img.flux import Flux1
        gi = set(inspect.signature(Flux1.generate_image).parameters)
        need = {"seed", "prompt", "num_inference_steps", "height", "width", "image_path"}
        ok = need.issubset(gi)
        print(f"  imagegen #42/#101: re-wired to new mflux — generate_image params {'MATCH ✅' if ok else 'MISMATCH'}; "
              f"img2img via image_path={'yes' if 'image_path' in gi else 'no'}. GPU+weights test pending.")
        return ok
    except Exception as e:
        print(f"  imagegen selftest: {str(e)[:90]}")
        return False


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
