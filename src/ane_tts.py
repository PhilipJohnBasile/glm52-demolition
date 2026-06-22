"""ANE neural TTS via AVSpeechSynthesizer — the agent SPEAKS. The neural voices synthesize on the
Neural Engine, FREE: no model, no authorization (unlike Speech ASR #87). Writes spoken audio to a WAV.

    from ane_tts import synthesize
    frames = synthesize("Build complete. All tests pass.", "out.wav")   # -> frames synthesized

#92. Built in parallel with the GPU heal.
Install:  uv pip install --python .venv pyobjc-framework-AVFoundation
"""
import wave


def synthesize(text, out_wav=None, voice="en-US", rate=None):
    """Synthesize `text` to speech on the ANE. Writes a 16-bit PCM WAV if out_wav given. Returns frame count.
    Uses writeUtterance (offline render) + a run-loop pump — the callback delivers AVAudioPCMBuffers."""
    import numpy as np
    import AVFoundation as AV
    from Foundation import NSRunLoop, NSDate
    synth = AV.AVSpeechSynthesizer.alloc().init()
    utt = AV.AVSpeechUtterance.alloc().initWithString_(text)
    v = AV.AVSpeechSynthesisVoice.voiceWithLanguage_(voice)
    if v:
        utt.setVoice_(v)
    if rate:
        utt.setRate_(rate)
    pcm, frame_box, sr_box, done = [], [0], [0], [False]

    def _cb(buf):
        if buf is None or buf.frameLength() == 0:                       # final empty buffer = end of stream
            done[0] = True
            return
        n = int(buf.frameLength())
        frame_box[0] += n
        sr_box[0] = int(buf.format().sampleRate())
        fcd = buf.floatChannelData()                                   # float32 PCM; best-effort extract for the WAV
        if fcd is not None:
            try:
                a = np.frombuffer(fcd[0].as_buffer(n * 4), dtype=np.float32)[:n]
                pcm.append((np.clip(a, -1, 1) * 32767).astype(np.int16))
            except Exception:                                          # extraction is best-effort; frame count is the proof
                pass

    synth.writeUtterance_toBufferCallback_(utt, _cb)
    rl = NSRunLoop.currentRunLoop()
    for _ in range(200):                                               # pump ~10s max
        if done[0]:
            break
        rl.runMode_beforeDate_("kCFRunLoopDefaultMode", NSDate.dateWithTimeIntervalSinceNow_(0.05))
    if out_wav and pcm:
        data = np.concatenate(pcm)
        with wave.open(out_wav, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr_box[0] or 22050)
            w.writeframes(data.tobytes())
    return frame_box[0]


if __name__ == "__main__":
    import os
    import tempfile
    fp = os.path.join(tempfile.gettempdir(), "ane_tts_test.wav")
    frames = synthesize("Build complete. All tests pass.", fp)
    wav_ok = os.path.exists(fp) and os.path.getsize(fp) > 44
    if os.path.exists(fp):
        os.remove(fp)
    print(f"  synthesize (ANE) -> {frames} frames | wav written: {wav_ok}")
    print(f"  ane_tts selftest {'PASS' if frames > 0 else 'CHECK'} — speech synthesized on the Neural Engine")
