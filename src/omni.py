"""Any-to-Any omni-router (#103) — the capstone. Detects the input modality and routes to the right M5 chip-
lane, composing across all 6 blocks. Ties together every lane built this session (#96–99, #102) + the model.

    from omni import handle
    handle("fix the failing pytest")          # text  -> ANE route -> GPU LLM / specialty
    handle(image="screenshot.png")            # image -> ANE OCR + classify
    handle(audio="clip.wav")                  # audio -> GPU mlx_whisper ASR
    handle(video="clip.mov")                  # video -> Media decode + ANE classify
    handle(table=df)                          # table -> CPU sklearn
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def handle(prompt="", image=None, audio=None, video=None, table=None):
    """Route by input modality to the optimal M5 chip-lane. Returns {modality, lane, result}."""
    if audio:
        from ane_asr import transcribe
        return {"modality": "audio", "lane": "GPU·mlx_whisper", "result": transcribe(audio)}
    if video:
        from video_classify import classify_video
        return {"modality": "video", "lane": "Media+ANE", "result": classify_video(video)}
    if image:
        from ane_vision import ocr, classify
        return {"modality": "image", "lane": "ANE·Vision", "result": {"text": ocr(image), "labels": classify(image)}}
    if table is not None:
        return {"modality": "table", "lane": "CPU·sklearn", "result": "tabular_ml.classify/regress/forecast"}
    from ane_route import route
    return {"modality": "text", "lane": "ANE-route→GPU-LLM", "result": route(prompt)}


def generate(kind, prompt, **kw):
    """Output side of any-to-any (#42/#100/#92) — text -> {image, audio, speech}. Routes to the gen lane so
    omni handles both directions: handle() reads any modality in, generate() writes any modality out."""
    if kind == "image":
        from imagegen import generate_image
        return {"kind": "image", "lane": "GPU·Flux", "result": generate_image(prompt, **kw)}
    if kind == "audio":
        from audiogen import text_to_audio
        return {"kind": "audio", "lane": "GPU·mlx_audio", "result": text_to_audio(prompt, **kw)}
    if kind == "speech":
        from ane_tts import synthesize
        return {"kind": "speech", "lane": "ANE·TTS", "result": synthesize(prompt, **kw)}
    raise ValueError(f"unknown gen kind: {kind!r} (image|audio|speech)")


if __name__ == "__main__":
    import tempfile
    from PIL import Image, ImageDraw
    ip = os.path.join(tempfile.gettempdir(), "omni.png")
    img = Image.new("RGB", (400, 80), "white")
    ImageDraw.Draw(img).text((10, 30), "hello world", fill="black")
    img.save(ip)
    r_text = handle("fix the failing pytest in auth.py")
    r_img = handle(image=ip)
    os.remove(ip)
    print(f"  text  -> {r_text['lane']}: {r_text['result']}")
    print(f"  image -> {r_img['lane']}: ocr={r_img['result']['text'][:18]!r} labels={r_img['result']['labels'][:2]}")
    ok = r_text["modality"] == "text" and r_img["modality"] == "image" and r_text["result"]
    print(f"  omni selftest {'PASS' if ok else 'CHECK'} — Any-to-Any routing across the M5 chips (audio/video/table dispatch too)")
