#!/usr/bin/env python3
"""#17 design-soul flywheel — make the model NATIVELY elite (verify-everything applied to design).

Mirrors the Lean flywheel (66/69): generate (CANON-steered) → audit_design gate → SELF-CORRECT from the
real violations → keep ONLY elite → SFT corpus → heal. After the heal the design PRIOR is elite, so the raw
model produces oklch/grid/scale designs with no prompt and no constraint = elite out of the box.

  python scripts/76_design_flywheel.py --selftest               # CPU: audit gate + self-correct + corpus logic
  python scripts/76_design_flywheel.py --n 200 --correct 2      # GPU: full flywheel (after miniF2F frees the GPU)
"""
import argparse
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from design_canon import CANON, audit_design  # noqa: E402

DESIGN_PROMPTS = [
    "A SaaS pricing page with three tiers.",
    "A dashboard card showing a KPI with a sparkline.",
    "A login form with email and password.",
    "A hero section for a developer-tools landing page.",
    "A settings panel with labelled toggles in sections.",
    "A pricing comparison table with a highlighted plan.",
    "A notification toast with icon, message, and dismiss.",
    "A profile card with avatar, name, bio, and two actions.",
]


def _post(base_url, model, msgs, max_tokens=1400):
    body = json.dumps({"model": model, "messages": msgs, "temperature": 0.6, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    import time as _t
    for a in range(4):                                       # retry transient server hiccups (hardened, like 66_prove)
        try:
            req = urllib.request.Request(base_url + "/chat/completions", body, {"Content-Type": "application/json"})
            m = json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]
            return m.get("content") or ""
        except Exception:  # noqa: BLE001
            if a == 3:
                raise
            _t.sleep(2 * (a + 1))


def extract_css(text):
    m = re.search(r"```(?:html|css)?\s*\n(.*?)```", text, re.S)
    return m.group(1).strip() if m else text.strip()


def prove_elite(base_url, model, prompt, correct=2, _gen=None):
    """Generate → audit → self-correct from the real violations → return (elite_code|None, trajectory).
    `_gen(msgs)->text` is injectable so the CPU selftest can run the whole loop with no model/GPU."""
    gen = _gen or (lambda msgs: _post(base_url, model, msgs))
    msgs = [{"role": "system", "content": CANON}, {"role": "user", "content": prompt}]
    for _ in range(correct + 1):
        out = gen(msgs)
        code = extract_css(out)
        v = audit_design(code)
        if not v:                                            # ELITE — keep it
            return code, msgs + [{"role": "assistant", "content": out}]
        msgs += [{"role": "assistant", "content": out},      # self-correct: feed the exact violations back
                 {"role": "user", "content": "Not elite yet — fix these and output ONLY the corrected code:\n- "
                  + "\n- ".join(v)}]
    return None, msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--correct", type=int, default=2)
    ap.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v4")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "heal", "design", "train.jsonl"))
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    kept = tries = 0
    with open(args.out, "w") as f:
        for i in range(args.n):
            prompt = DESIGN_PROMPTS[i % len(DESIGN_PROMPTS)]
            tries += 1
            code, traj = prove_elite(args.base_url, args.model, prompt, args.correct)
            if code:                                         # keep ONLY verified-elite → the heal corpus
                f.write(json.dumps({"messages": traj}) + "\n")
                kept += 1
            print(f"  [{i + 1}/{args.n}] {'✓ elite' if code else '✗ gave up'}  ({kept}/{tries} kept)", flush=True)
    print(f"\n  DESIGN-FLYWHEEL: {kept}/{tries} elite designs → {args.out}  (SFT this → native-elite prior)")


def _selftest():
    elite = (":root{--brand:oklch(0.62 0.19 255)}\n.card{padding:16px;margin:24px 0;gap:8px;"
             "border:1px solid oklch(0.9 0.02 255);font-size:16px;color:oklch(0.2 0.02 255)}")
    bad = ".card{padding:13px;margin:5px;background:#fff;color:rgb(0,0,0);font-size:17px}"
    assert audit_design(elite) == [] and len(audit_design(bad)) == 3
    # the self-correct loop: mock a model that emits BAD first, then ELITE after seeing violations
    seq = iter([f"```css\n{bad}\n```", f"```css\n{elite}\n```"])
    code, traj = prove_elite("", "", DESIGN_PROMPTS[0], correct=2, _gen=lambda msgs: next(seq))
    assert code is not None and audit_design(code) == [], code
    assert sum(1 for m in traj if m["role"] == "user") == 2, "should have fed violations back once"
    # corpus filter: a model that never gets it right → nothing kept
    code2, _ = prove_elite("", "", DESIGN_PROMPTS[0], correct=1, _gen=lambda msgs: f"```css\n{bad}\n```")
    assert code2 is None
    print("  design_flywheel selftest PASS — audit gate + self-correct-from-violations + keep-only-elite, GPU-free")
    print("  (generate-step needs the GPU; run after miniF2F → heal/design/train.jsonl → SFT = native-elite prior)")


if __name__ == "__main__":
    main()
