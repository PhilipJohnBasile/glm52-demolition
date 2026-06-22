"""Sound-flywheel — expand the sound gold the compounding way: the model writes sound-making code for a
canon-grounded brief, we RUN it in a subprocess, and verify('sound') keeps only audio that passes
(loudness / earcon). gen → run → verify → keep. GPU-gated (needs the model); slots into the chain after the
repair soul, then the sound soul is healed on the result.

  python scripts/sound_flywheel.py --selftest     # CPU-only: prove the run+verify harness (no model)
  python scripts/sound_flywheel.py --target 150    # GPU: fill the gold
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from sound_verify import verify_earcon, verify_loudness

# (brief, kind, why) — grounded in the elite_sound canon
BRIEFS = [
    ("A warm 'success' earcon under 1 second — a major arpeggio, clean attack.", "earcon", "Eno — the earcon: identity + feedback in a moment"),
    ("A soft 'error' tone, gentle not harsh — a brief minor interval that signals without alarming.", "earcon", "Herrmann — dissonance as controlled signal"),
    ("A friendly robot acknowledgement beep, curious and warm, à la WALL·E.", "earcon", "Ben Burtt — sound as character; emotion in timbre"),
    ("A bright reward/coin chime, ~0.5 s, instantly positive.", "earcon", "Koji Kondo — the functional earworm"),
    ("A short airy UI 'whoosh' for a screen transition, ~0.4 s.", "earcon", "Foley — the tactile world made audible"),
    ("A 2-second calm ambient pad for a focus app, slowly evolving, never harsh.", "loud", "Eno — ambient as a place, not a foreground"),
    ("A gentle notification ping, single note, friendly, ~0.3 s.", "earcon", "the earcon — less is more"),
    ("A soft 'startup' chord that means 'ready', calming (à la the Mac chime).", "earcon", "Jim Reekes — a palate-cleanser that says the wait is over"),
]

PROMPT = ("Write Python that synthesizes the described sound and writes a 44100 Hz wav to the path in the "
          "variable OUT_WAV (use numpy + soundfile; keep peaks below 1.0). {brief}\n"
          "Output ONLY a single ```python code block.")

SYS = "You compose and design sound. Return runnable code that makes the sound, grounded in a master's principle."


def _run_and_verify(code, kind):
    out = tempfile.mktemp(suffix=".wav")
    pyf = tempfile.mktemp(suffix=".py")
    with open(pyf, "w") as f:
        f.write(f"OUT_WAV = {out!r}\n" + code)
    try:
        r = subprocess.run([sys.executable, pyf], capture_output=True, timeout=15)
        if r.returncode != 0 or not os.path.exists(out):
            return (False, {})
        return verify_earcon(out) if kind == "earcon" else verify_loudness(out)
    except Exception:
        return (False, {})
    finally:
        for p in (pyf, out):
            if os.path.exists(p):
                os.remove(p)


def _extract(text):
    m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
    return m.group(1).strip() if m else None


def _selftest():
    good = ("import numpy as np, soundfile as sf\n"
            "rate=44100; notes=[523,659,784]\n"
            "seg=lambda f: 0.3*np.sin(2*np.pi*f*np.linspace(0,0.18,int(0.18*rate),False))*np.hanning(int(0.18*rate))\n"
            "sf.write(OUT_WAV, np.concatenate([seg(f) for f in notes]), rate)")
    bad_clip = "import numpy as np, soundfile as sf\nsf.write(OUT_WAV, 5*np.ones(44100*3), 44100)"   # clip + too long
    bad_err = "raise RuntimeError('bad code')"
    g, gm = _run_and_verify(good, "earcon")
    b1, _ = _run_and_verify(bad_clip, "earcon")
    b2, _ = _run_and_verify(bad_err, "earcon")
    ok = g and not b1 and not b2
    print(f"  harness: good={g}{gm} · clip={b1} · crash={b2} -> {'PASS ✅' if ok else 'CHECK'} "
          f"(keeps only code that runs AND sounds right)")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=150)
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v4")
    ap.add_argument("--adapter", default="heal/adapters-soul2")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if _selftest() else 1)
    from mlx_lm import generate, load
    model, tok = load(a.model, adapter_path=a.adapter)
    os.makedirs("heal/gold_sound", exist_ok=True)
    kept, seen, tries = [], set(), 0
    while len(kept) < a.target and tries < a.target * 12:
        tries += 1
        brief, kind, why = random.choice(BRIEFS)
        prompt = tok.apply_chat_template(
            [{"role": "system", "content": SYS}, {"role": "user", "content": PROMPT.format(brief=brief)}],
            add_generation_prompt=True, tokenize=False)
        code = _extract(generate(model, tok, prompt=prompt, max_tokens=400, verbose=False))
        if not code or code in seen:
            continue
        seen.add(code)
        ok, _ = _run_and_verify(code, kind)
        if ok:
            kept.append({"messages": [
                {"role": "system", "content": SYS},
                {"role": "user", "content": brief},
                {"role": "assistant", "content": f"```python\n{code}\n```\n\n**Why:** {why}"}]})
            if len(kept) % 10 == 0:
                print(f"  {len(kept)}/{a.target} kept ({tries} tries)", flush=True)
    with open("heal/gold_sound/sound.jsonl", "a") as w:
        for r in kept:
            w.write(json.dumps(r) + "\n")
    print(f"  sound-flywheel done: +{len(kept)} validated examples ({tries} tries) -> heal/gold_sound/sound.jsonl")


if __name__ == "__main__":
    main()
