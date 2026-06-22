"""verify('sound', …) — the audio facet's validator (the sound twin of the design render→critique loop).
Checks an artifact against the `research/elite_sound.md` canon on three axes:
  · HARMONY  — music21: in-key + no parallel fifths/octaves between outer voices (Bach-correct voice-leading)
  · LOUDNESS — pyloudnorm: integrated LUFS in a safe band + no clipping (the broadcast/UI norm)
  · FEEL     — the Dilla check: dead-grid quantization (zero micro-timing variance) = soulless; reward the wobble
Runs on CPU (an "other chip" while the GPU heals). Good+bad audited in selftest().
"""
import numpy as np


def _pm(n):
    from music21 import pitch
    p = pitch.Pitch()
    p.midi = int(n)
    return p


def verify_harmony(chords, key="C"):
    """chords: list of [midi,…] low→high. Returns (passed, issues). In-key + no parallel 5ths/8ves (outer voices)."""
    from music21 import key as m21key, voiceLeading
    k = m21key.Key(key)
    scale_pcs = {p.pitchClass for p in k.pitches}
    issues = []
    for ch in chords:
        for n in ch:
            if (int(n) % 12) not in scale_pcs:
                issues.append(f"out-of-key pc {int(n) % 12}")
    for a, b in zip(chords, chords[1:]):
        vlq = voiceLeading.VoiceLeadingQuartet(_pm(min(a)), _pm(min(b)), _pm(max(a)), _pm(max(b)))
        if vlq.parallelFifth():
            issues.append("parallel fifth (bass∥soprano)")
        if vlq.parallelOctave():
            issues.append("parallel octave (bass∥soprano)")
    return (len(issues) == 0, issues)


def verify_loudness(wav, target=-16.0, tol=7.0):
    """pyloudnorm: integrated LUFS within [target±tol] and no clipping. Returns (passed, metrics)."""
    import soundfile as sf
    import pyloudnorm as pyln
    data, rate = sf.read(wav)
    loud = float(pyln.Meter(rate).integrated_loudness(data))
    peak = float(np.max(np.abs(data)))
    ok = (target - tol) <= loud <= (target + tol) and peak < 0.99
    return (ok, {"lufs": round(loud, 1), "peak": round(peak, 3)})


def verify_feel(onsets, min_jitter_ms=1.5):
    """The Dilla check: a perfectly-quantized grid (≈0 ms jitter) is soulless. Reward humanized micro-timing."""
    d = np.diff(np.asarray(onsets, dtype=float))
    if len(d) < 2:
        return (True, {"note": "too few onsets"})
    jit = float(np.std(d) * 1000)
    return (jit >= min_jitter_ms, {"jitter_ms": round(jit, 2)})


def verify_earcon(wav, max_sec=1.5):
    """An earcon must be short with a clear attack (Eno/Win95 discipline)."""
    import soundfile as sf
    data, rate = sf.read(wav)
    if data.ndim > 1:
        data = data.mean(axis=1)
    dur = len(data) / rate
    env = np.abs(data)
    attack_ok = env[: int(0.05 * rate)].max() > 0.2 * env.max() if env.max() > 0 else False
    return (dur <= max_sec and attack_ok, {"sec": round(dur, 2), "attack": bool(attack_ok)})


def selftest():
    import os
    import tempfile
    import soundfile as sf
    # HARMONY — good: in-key, outer voices in parallel tenths (no 5ths/8ves); bad: parallel perfect fifths
    good = [[48, 55, 64], [53, 60, 69], [55, 62, 71], [48, 55, 64]]
    bad = [[48, 55], [50, 57], [52, 59]]
    gh, _ = verify_harmony(good)
    bh, bi = verify_harmony(bad)
    # LOUDNESS — good: quiet sine ~safe; bad: clipped/hot
    rate = 44100
    t = np.linspace(0, 2, 2 * rate, False)
    gp = tempfile.mktemp(suffix=".wav")
    sf.write(gp, 0.12 * np.sin(2 * np.pi * 440 * t), rate)
    bp = tempfile.mktemp(suffix=".wav")
    sf.write(bp, np.clip(12 * np.sin(2 * np.pi * 440 * t), -1, 1), rate)
    gl, glm = verify_loudness(gp)
    bl, blm = verify_loudness(bp)
    os.remove(gp)
    os.remove(bp)
    # FEEL — good: humanized jitter; bad: dead grid
    gf, _ = verify_feel([0, 0.5, 1.01, 1.49, 2.02])
    bf, _ = verify_feel([0, 0.5, 1.0, 1.5, 2.0])
    ok = gh and not bh and gl and not bl and gf and not bf
    print(f"  harmony  good={gh}  bad={bh} {bi[:1]}")
    print(f"  loudness good={gl}{glm}  bad={bl}{blm}")
    print(f"  feel     good={gf}  bad={bf} (dead grid)")
    print(f"  sound_verify {'PASS ✅' if ok else 'CHECK'} — discriminates good↔bad on all 3 axes (Bach + broadcast + Dilla)")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
