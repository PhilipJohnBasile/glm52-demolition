"""Build SOUND GOLD — code-rendered music/SFX seed examples from the `research/elite_sound.md` canon, each
VALIDATED by sound_verify (Bach harmony / broadcast loudness / Dilla feel / earcon). The canon→gold step for
the sound facet, so the sound soul is heal-ready when the GPU frees. CPU-only (other-chip work, GPU-free).

  python scripts/build_sound_gold.py
"""
import json
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import soundfile as sf
from sound_verify import verify_earcon, verify_feel, verify_harmony

SYS = ("You compose and design sound. Return runnable code that makes the sound, grounded in a named master's "
       "principle from the elite-sound canon.")


def ex_cadence():
    chords = [[48, 55, 64], [53, 60, 69], [55, 62, 71], [48, 55, 64]]      # I IV V I, outer voices in tenths
    code = ("from music21 import chord, stream\n"
            f"prog = {chords}  # C major: I IV V I\n"
            "s = stream.Stream([chord.Chord(c) for c in prog])\n"
            "s.write('midi', 'cadence.mid')")
    return ("A resolved 4-chord cadence in C major, Bach-correct voice-leading (no parallel fifths).", code,
            "Bach — counterpoint as architecture; the cadence resolves and the outer voices avoid parallel "
            "perfect intervals.", verify_harmony(chords)[0])


def ex_earcon():
    rate, notes = 44100, [523, 659, 784]
    seg = lambda f: 0.3 * np.sin(2 * np.pi * f * np.linspace(0, 0.18, int(0.18 * rate), False)) * np.hanning(int(0.18 * rate))
    fp = tempfile.mktemp(suffix=".wav")
    sf.write(fp, np.concatenate([seg(f) for f in notes]), rate)
    ok = verify_earcon(fp)[0]
    os.remove(fp)
    code = ("import numpy as np, soundfile as sf\n"
            "rate, notes = 44100, [523, 659, 784]  # C E G ascending\n"
            "seg = lambda f: 0.3*np.sin(2*np.pi*f*np.linspace(0,0.18,int(0.18*rate),False))*np.hanning(int(0.18*rate))\n"
            "sf.write('success.wav', np.concatenate([seg(f) for f in notes]), rate)")
    return ("A warm 'success' earcon under 1 second — a major arpeggio with a clean attack.", code,
            "Eno / the earcon — identity + feedback + personality in under a second; a major arpeggio reads as "
            "resolved and positive.", ok)


def ex_swing():
    onsets = [0.0, 0.49, 1.02, 1.48, 2.03, 2.51]                            # humanized, not dead-grid
    code = ("import numpy as np\n"
            "# J Dilla: push/drag hits off the grid — the wobble is the soul\n"
            "grid = np.arange(0, 3, 0.5)\n"
            "onsets = grid + np.random.uniform(-0.025, 0.025, len(grid))  # micro-timing jitter")
    return ("A 4-on-the-floor beat with HUMAN swing (J Dilla), not a dead quantized grid.", code,
            "J Dilla — the humanized grid; micro-timing variance is what makes a beat breathe instead of tick.",
            verify_feel(onsets)[0])


def ex_leitmotif():
    motif = [[60], [62], [64], [67]]                                       # rising C D E G, in key
    code = ("from music21 import note, stream\n"
            "motif = [60, 62, 64, 67]  # rising contour = aspiration (the Force-theme shape)\n"
            "s = stream.Stream([note.Note(m) for m in motif])\n"
            "s.write('midi', 'hero_theme.mid')")
    return ("A 4-note leitmotif for a brave hero, in C major (Wagner → Williams).", code,
            "Wagner → Williams — the leitmotif; a short, rising, recurring idea becomes the character's identity.",
            verify_harmony(motif)[0])


def main():
    os.makedirs("heal/gold_sound", exist_ok=True)
    rows = []
    for fn in (ex_cadence, ex_earcon, ex_swing, ex_leitmotif):
        brief, code, why, ok = fn()
        if not ok:
            print(f"  SKIP (validator failed): {brief[:42]}")
            continue
        rows.append({"messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content": brief},
            {"role": "assistant", "content": f"```python\n{code}\n```\n\n**Why:** {why}"}]})
    with open("heal/gold_sound/sound.jsonl", "w") as w:
        for r in rows:
            w.write(json.dumps(r) + "\n")
    print(f"  wrote {len(rows)}/4 validated sound-gold examples -> heal/gold_sound/sound.jsonl")


if __name__ == "__main__":
    main()
