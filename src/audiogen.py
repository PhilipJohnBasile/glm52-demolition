"""GPU audio generation (#100) — text-to-audio (TTS) via mlx_audio on the GPU. Complements the ANE TTS (#92,
fast/offline, Apple voices) with higher-quality GPU models (Kokoro etc.). Test-pending: needs the GPU free +
a one-time model download on first call (the heal chain owns the GPU right now).

    from audiogen import text_to_audio
    text_to_audio("hello from the demolished model", out="/tmp/out.wav")
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

DEFAULT_MODEL = "mlx-community/Kokoro-82M-bf16"


def text_to_audio(text, out="/tmp/audiogen.wav", model=DEFAULT_MODEL, voice="af_heart", max_tokens=1200):
    """GPU TTS via mlx_audio.tts.generate_audio -> writes a wav, returns the path. (GPU + model download.)"""
    from mlx_audio.tts.generate import generate_audio
    pref = out[:-4] if out.endswith(".wav") else out
    generate_audio(text=text, model=model, voice=voice, max_tokens=max_tokens,
                   file_prefix=pref, audio_format="wav", verbose=False)
    return out


if __name__ == "__main__":
    import inspect
    from mlx_audio.tts.generate import generate_audio
    params = inspect.signature(generate_audio).parameters
    ok = "text" in params and "model" in params and "voice" in params
    print(f"  audiogen #100: generate_audio wired (text -> wav via {DEFAULT_MODEL}); "
          f"import+sig {'OK' if ok else 'BAD'} — GPU+download test pending (chain owns the GPU)")
