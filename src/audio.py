"""Voice I/O — fully local on the M5, no cloud:
  - transcribe(audio) : speech -> text via Whisper on MLX (Apple-Silicon optimized).
  - speak(text)       : text -> speech via macOS `say` (instant, built-in) or mlx_audio (neural).
"""
import os
import subprocess


def transcribe(audio_path, model="mlx-community/whisper-large-v3-turbo"):
    """Speech -> text (Whisper / MLX). Model auto-downloads on first use (~1.5 GB for turbo)."""
    try:
        import mlx_whisper
    except Exception as e:  # noqa: BLE001
        return f"mlx_whisper unavailable: {e}"
    if not os.path.exists(audio_path):
        return f"no such audio file: {audio_path}"
    try:
        r = mlx_whisper.transcribe(audio_path, path_or_hf_repo=model)
        return (r.get("text") or "").strip() or "(no speech detected)"
    except Exception as e:  # noqa: BLE001
        return f"transcribe error: {str(e)[:200]}"


def speak(text, path=None, neural=False):
    """Text -> speech. macOS `say` by default (instant, free); mlx_audio for neural quality."""
    if neural:
        try:
            from mlx_audio.tts.generate import generate_audio
            out = (path or "/tmp/tts").rsplit(".", 1)[0]
            generate_audio(text=text, file_prefix=out, audio_format="wav", join_audio=True)
            return out + ".wav"
        except Exception:  # noqa: BLE001
            pass                                            # fall back to `say`
    out = path or "/tmp/tts.aiff"
    try:
        subprocess.run(["say", "-o", out, text], timeout=60, check=True)
        return out
    except Exception as e:  # noqa: BLE001
        return f"speak error: {str(e)[:120]}"


def selftest():
    out = speak("trust layer online")                       # `say` needs no GPU/model
    ok = isinstance(out, str) and os.path.exists(out)
    print(f"  audio selftest: speak(say)={ok} -> {out}  (transcribe needs a whisper download)"
          f"  {'PASS ✅' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
