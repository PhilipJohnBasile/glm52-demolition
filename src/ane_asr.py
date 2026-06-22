"""ASR (#99) — Automatic Speech Recognition via mlx_whisper on the GPU/MLX. No Apple-Speech permission needed
(supersedes the auth-blocked #87). Pairs with ANE VAD (#91) to gate it; Audio-Text-to-Text = transcribe → LLM.

    from ane_asr import transcribe
    text = transcribe("clip.wav")   # -> recognized text
"""


def transcribe(audio_path, model="mlx-community/whisper-tiny"):
    """Transcribe speech to text via mlx_whisper (Whisper on MLX/GPU). Returns the recognized text.
    Loads the WAV directly (wave + resample to 16 kHz) so it needs NO ffmpeg."""
    import wave
    import numpy as np
    import mlx_whisper
    with wave.open(audio_path, "rb") as w:
        sr = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    if sr != 16000:
        import scipy.signal as sg
        pcm = sg.resample_poly(pcm, 16000, sr).astype(np.float32)
    r = mlx_whisper.transcribe(pcm, path_or_hf_repo=model)
    return (r.get("text", "") or "").strip()


if __name__ == "__main__":
    import os
    import sys
    import tempfile
    sys.path.insert(0, os.path.dirname(__file__))
    from ane_tts import synthesize                                   # TTS -> ASR round-trip
    fp = os.path.join(tempfile.gettempdir(), "asr_test.wav")
    synthesize("the quick brown fox jumps over the lazy dog", fp)
    text = transcribe(fp)
    if os.path.exists(fp):
        os.remove(fp)
    print(f"  ASR (mlx_whisper) -> {text!r}")
    hit = "fox" in text.lower() and "quick" in text.lower()    # round-trip recognized the sentence
    print(f"  ane_asr selftest {'PASS' if hit else 'CHECK'} — speech recognized (TTS→ASR round-trip)")
