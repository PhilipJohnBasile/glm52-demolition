#!/usr/bin/env python3
"""Per-facet soul flywheel — generalizes 76_design_flywheel to EVERY facet (src/soul.py).

For each facet: generate (facet.canon, which names its masters → activates the latent knowledge) → facet.audit
gate → SELF-CORRECT from the real violations → keep ONLY elite → heal/<facet>/soul.jsonl. Loops all facets so
the whole model goes elite across the board on one GPU pass, then SFT each → adapters-<facet>. Mirrors the Lean
(66/69) and design (76) flywheels; reuses their retry-hardened client + accept/reject structure.

  python scripts/77_soul_flywheel.py --selftest                 # CPU: the per-facet loop logic (no model)
  python scripts/77_soul_flywheel.py --facets dataviz,security  # GPU: run specific facets (after miniF2F)
  python scripts/77_soul_flywheel.py --n 120 --correct 2        # GPU: all facets
"""
import argparse
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from soul import FACETS  # noqa: E402

# a few elite generation prompts per facet (the model produces, the gate keeps only the elite)
PROMPTS = {
    "design": ["A SaaS pricing page in the Swiss International style.", "A Rams-minimal settings panel.",
               "A dashboard KPI card.", "A De Stijl composition.", "An editorial pricing table, Vignelli-grade."],
    "dataviz": ["A Tufte-clean line chart of monthly revenue.", "Small multiples of regional sales.",
                "A horizontal bar chart ranking products, direct-labelled.", "A slope chart of before/after."],
    "code": ["Merge overlapping intervals.", "An LRU cache.", "A retry decorator with backoff.",
             "Parse a CSV line respecting quotes."],
    "security": ["A session-token verifier.", "Look up a user by id from the database.",
                 "Hash and verify a password.", "Validate and sanitize an uploaded filename."],
    "math": ["Prove the sum of the first n odd numbers is n^2.", "Prove a + b = b + a for naturals.",
             "Prove n^2 is even iff n is even."],
    "prose": ["Explain what a parser does, plainly.", "Write release notes for a bug fix.",
              "Describe the dependency rule in two sentences."],
    "architecture": ["Sketch a hexagonal architecture for an order service.",
                     "Design the module boundaries for a CSV-import pipeline.", "Apply the dependency rule to a payments flow."],
    "research": ["Does chain-of-thought prompting improve LLM reasoning? Cite the source; separate shown from speculated.",
                 "What does the LoRA paper actually claim about parameter efficiency — and what does it NOT claim?",
                 "Summarize what RLHF demonstrably achieves vs what remains speculative, with citations."],
    # NOTE research's FULL gate is groundedness vs a retrieved source (the science-QA flywheel pairs each Q with an
    # arXiv abstract → the answer's claims must appear in it → no hallucinated citations). audit_research is the static proxy.
}


def _post(base_url, model, msgs, max_tokens=1400):
    body = json.dumps({"model": model, "messages": msgs, "temperature": 0.6, "max_tokens": max_tokens,
                       "repetition_penalty": 1.3,            # break degeneration loops (demolished 3-bit on long gens)
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    import time as _t
    for a in range(4):                                       # retry transient hiccups (hardened, like 66/76)
        try:
            req = urllib.request.Request(base_url + "/chat/completions", body, {"Content-Type": "application/json"})
            m = json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]
            return m.get("content") or ""
        except Exception:  # noqa: BLE001
            if a == 3:
                raise
            _t.sleep(2 * (a + 1))


def extract_code(text):
    m = re.search(r"```[a-zA-Z]*\s*\n(.*?)```", text, re.S)
    return m.group(1).strip() if m else text.strip()


def _repetitive(text, ng=4, cap=4):
    """Degeneration guard the audits lack: True if any ng-gram repeats >cap times (a loop)."""
    from collections import Counter
    w = text.split()
    if len(w) < 2 * ng:
        return False
    return Counter(tuple(w[i:i + ng]) for i in range(len(w) - ng + 1)).most_common(1)[0][1] > cap


def prove_elite(base_url, model, facet, prompt, correct=2, _gen=None):
    """Generate (facet.canon) → facet.audit → self-correct from violations → return (elite|None, trajectory).
    `_gen(msgs)->text` injectable so the CPU selftest runs the whole loop with no model."""
    gen = _gen or (lambda msgs: _post(base_url, model, msgs))
    msgs = [{"role": "system", "content": facet.canon}, {"role": "user", "content": prompt}]
    for attempt in range(correct + 1):
        out = gen(msgs)
        code = extract_code(out)
        v = facet.audit(code)
        if _repetitive(out):                                 # degeneration guard (the audits miss loops)
            v = v + ["degenerate repetition loop — write varied, non-repeating content"]
        print(f"    [{facet.name} a{attempt}] {'ELITE ✓' if not v else 'reject: ' + ' | '.join(v[:2])}"
              f"  ({len(out)} ch)  {' '.join(out.split())[:130]!r}", flush=True)
        if not v:                                            # ELITE per this facet's gate
            return code, msgs + [{"role": "assistant", "content": out}]
        msgs += [{"role": "assistant", "content": out},
                 {"role": "user", "content": "Not elite yet — fix these and output ONLY the corrected code:\n- " + "\n- ".join(v)}]
    return None, msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--facets", default="", help="comma list; default = all")
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--correct", type=int, default=2)
    ap.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v4")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    names = args.facets.split(",") if args.facets else list(FACETS)
    for name in names:
        facet = FACETS[name]
        prompts = PROMPTS.get(name, [])
        outdir = os.path.join(os.path.dirname(__file__), "..", "heal", name)
        os.makedirs(outdir, exist_ok=True)
        kept = tries = 0
        tmp = os.path.join(outdir, "soul.jsonl.tmp")
        with open(tmp, "w") as f:
            for i in range(args.n):
                prompt = prompts[i % len(prompts)] if prompts else "Produce an elite example."
                tries += 1
                code, traj = prove_elite(args.base_url, args.model, facet, prompt, args.correct)
                if code:
                    f.write(json.dumps({"messages": traj}) + "\n")
                    kept += 1
        os.replace(tmp, os.path.join(outdir, "soul.jsonl"))   # atomic — a kill mid-run keeps the PRIOR soul.jsonl intact
        print(f"  {name:13s}: {kept}/{tries} elite → heal/{name}/soul.jsonl", flush=True)
    print("  DONE — SFT each heal/<facet>/soul.jsonl → adapters-<facet> (or merge) = elite across every facet")


def _selftest():
    # mock a model that emits BAD then ELITE for a gated facet (security), proving the per-facet loop works
    bad = 'token = "sk-ant-api03-abc1234567890XYZdefghij"'
    good = "token = os.environ['API_KEY']; cur.execute('select 1 where id=%s', (uid,))"
    seq = iter([f"```python\n{bad}\n```", f"```python\n{good}\n```"])
    code, traj = prove_elite("", "", FACETS["security"], PROMPTS["security"][0], correct=2, _gen=lambda m: next(seq))
    assert code is not None and FACETS["security"].audit(code) == [], code
    assert sum(1 for m in traj if m["role"] == "user") == 2, "should feed violations back once"
    # a facet with a clean first try (prose) keeps it immediately
    clean = "The parser reads one token at a time. It stops on the first it cannot place."
    code2, _ = prove_elite("", "", FACETS["prose"], PROMPTS["prose"][0], correct=1, _gen=lambda m: clean)
    assert code2 is not None
    print(f"  facets ready: {list(FACETS)}")
    print("  soul_flywheel selftest PASS — per-facet generate→gate→self-correct→keep-elite loop works across facets")
    print("  (generate-step needs the GPU; run after miniF2F → heal/<facet>/soul.jsonl → SFT = elite everywhere)")


if __name__ == "__main__":
    main()
