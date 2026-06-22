#!/usr/bin/env python3
"""Soul-retention scorecard — measure how much elite training survives across the Demolition family (#53-58).

The family's whole premise is "shrink but keep the soul." This MEASURES it: for each model (99GB baseline +
each shrunken size), generate per-facet outputs and score them through the SAME soul gates that defined elite
(soul.FACETS[f].audit) → % elite per facet per size. Reuses the verify-everything machinery on the family
itself, so the claim "64/48/28 stay elite, 14/7 are the experiment" becomes a number, not a hope.

Gateable facets (design/dataviz/security/prose/research) score statically here; code/math delegate to the live
verifiers (HumanEval / Lean — run 58_bench + 73_minif2f per model). GPU to generate; the SCORING is CPU.

  python scripts/80_family_eval.py --selftest                       # CPU: the scoring logic (mock outputs)
  python scripts/80_family_eval.py --models models/GLM-5.2-q3a4-v4   # GPU: score one served model
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from soul import FACETS  # noqa: E402

_spec = importlib.util.spec_from_file_location("fly", os.path.join(HERE, "77_soul_flywheel.py"))
_fly = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fly)
PROMPTS = _fly.PROMPTS

GATEABLE = ("design", "dataviz", "security", "prose", "research")   # static gate == the eval here


def _post(base_url, model, canon, prompt, max_tokens=1200):
    body = json.dumps({"model": model, "messages": [{"role": "system", "content": canon},
                       {"role": "user", "content": prompt}], "temperature": 0.4, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    import time as _t
    for a in range(4):
        try:
            req = urllib.request.Request(base_url + "/chat/completions", body, {"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"].get("content") or ""
        except Exception:  # noqa: BLE001
            if a == 3:
                raise
            _t.sleep(2 * (a + 1))


def _extract(text):
    m = re.search(r"```[a-zA-Z]*\s*\n(.*?)```", text, re.S)
    return m.group(1).strip() if m else text.strip()


def score_model(base_url, model, n=4, _gen=None):
    """Return {facet: (elite_count, n)} over the gateable facets — % elite = soul retained for that facet."""
    gen = _gen or (lambda canon, prompt: _post(base_url, model, canon, prompt))
    card = {}
    for facet in GATEABLE:
        prompts = PROMPTS.get(facet, [])[:n]
        if not prompts:
            continue
        elite = sum(1 for p in prompts if not FACETS[facet].audit(_extract(gen(FACETS[facet].canon, p))))
        card[facet] = (elite, len(prompts))
    return card


def _print_card(name, card):
    total_e = sum(e for e, _ in card.values())
    total_n = sum(n for _, n in card.values())
    print(f"  {name}:  soul-retention {total_e}/{total_n} = {100 * total_e / max(total_n, 1):.0f}%")
    for facet, (e, n) in card.items():
        print(f"      {facet:9s} {e}/{n} {'█' * e}{'░' * (n - e)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--models", nargs="*", default=["models/GLM-5.2-q3a4-v4"])
    ap.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--n", type=int, default=4)
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    for m in a.models:                                   # serve each, then eval (one at a time on the GPU)
        _print_card(os.path.basename(m), score_model(a.base_url, m, a.n))
    print("  → compare across the family: 64/48/28 should hold high; 14/7 reveal where the soul breaks")


def _selftest():
    # mock a model: emits elite for design/research, sloppy for prose → the scorecard reflects it
    def fake(canon, prompt):
        if "ELITE product designer" in canon:
            return "```css\n.x{padding:16px;color:oklch(0.2 0.02 255);font-size:16px}\n```"
        if "careful RESEARCHER" in canon:
            return "Per Wei et al. (2022, arXiv:2201.11903), CoT helps large models on GSM8K; it does not make reasoning reliable."
        if "ELITE prose" in canon:
            return "Let's delve into this rich tapestry and leverage synergies."          # AI-slop → not elite
        return "ok"
    card = score_model("", "", n=2, _gen=fake)
    assert card["design"][0] == 2, card            # elite designs pass
    assert card["research"][0] == 2, card           # cited+hedged passes
    assert card["prose"][0] == 0, card              # slop fails → soul NOT retained for prose
    _print_card("mock", card)
    print("  family_eval selftest PASS — scores soul-retention per facet via the soul gates (verify-everything on the family)")


if __name__ == "__main__":
    main()
