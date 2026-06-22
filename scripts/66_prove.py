#!/usr/bin/env python3
"""Proof harness (#30 + #29) — generate Lean 4 proofs, verify_lean checks, with BEST-OF-N +
verifier-guided SELF-CORRECTION (feed the real Lean error back → the model revises). The test-time
loop that takes pass@1 → high — the Goedel-Prover recipe, fully local + MLX-bounded.

  python scripts/66_prove.py --n 5 --attempts 3 --correct 2 --base-url http://127.0.0.1:8080/v1
"""
import argparse
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from verifiers import verify_lean  # noqa: E402

SMOKE = [
    "theorem id_ex (n : Nat) : n = n",
    "theorem two_eq : 1 + 1 = 2",
    "theorem zero_add_ex (n : Nat) : 0 + n = n",
    "theorem add_comm_ex (a b : Nat) : a + b = b + a",
    "theorem and_comm_ex (p q : Prop) (h : p ∧ q) : q ∧ p",
]

SYS = ("You are an expert Lean 4 prover (mathlib available). Prove the theorem. Tactics: rfl; omega (linear "
       "arith over Nat/Int — a+b=b+a, 0+n=n); ring/ring_nf (ring identities); linarith/nlinarith (real "
       "inequalities, e.g. `nlinarith [sq_nonneg (a-b)]`); positivity (≥0 goals); field_simp; simp/simp_all; "
       "decide; term-mode (`exact ⟨h.2, h.1⟩`). Output ONLY a ```lean block with the full `theorem ... := by ...`. No prose.")


# Cold-start breaker (novel plateau-fix): the generic single-line tactics that close most arithmetic/logic
# goals. When the MODEL can't find one (e.g. keeps trying rfl on 0+n=n), brute-forcing these GUARANTEES a
# verified proof to TRAIN on — bootstrapping the tactic the model couldn't discover on its own.
CORE_TACTICS = ["rfl", "omega", "decide", "simp", "norm_num", "tauto", "simp_all", "trivial",
                "ring", "ring_nf", "linarith", "nlinarith", "positivity", "field_simp", "gcongr", "aesop",
                "induction n <;> simp", "induction n <;> omega", "constructor <;> assumption"]


def enumerate_tactics(stmt):
    """Brute-force the core tactics on `stmt` via Lean (no model). Returns the first verified `head := by <tac>`,
    else None. The cold-start bootstrap: omega/simp/tauto/decide solve exactly the goals the model keeps missing,
    so the resulting proof seeds expert-iteration with the tactic it couldn't reach. Pure CPU (Lean), GPU-free."""
    head = stmt.split(":=")[0].strip()
    for tac in CORE_TACTICS:
        proof = f"{head} := by {tac}"
        if getattr(verify_lean(proof), "passed", False):
            return proof
    return None


def augment_coldstart(stmt, k=5):
    """Novel cold-start data augmentation: when enumerate_tactics solves a stuck theorem, expand it into up to
    k Lean-verified VARIATIONS (rename the bound Nat var + theorem name) so ONE guaranteed proof becomes a
    CLUSTER of training signal — strong enough to overcome the model's prior (a lone example dilutes among
    ~3800 SFT rows). Each variation is Lean-checked. Returns [proof, variant…]. The fix if 1 copy plateaus."""
    proof0 = enumerate_tactics(stmt)
    if not proof0:
        return []
    head = stmt.split(":=")[0].strip()
    tac = proof0.split(":= by")[-1].strip()
    var_m = re.search(r"\((\w+)\s*:\s*Nat\)", head)
    name_m = re.search(r"theorem\s+(\w+)", head)
    out = [proof0]
    if var_m and name_m:
        old, name = var_m.group(1), name_m.group(1)
        variants = []
        for nv in [v for v in ("m", "k", "x", "y", "z") if v != old][:k]:
            h = re.sub(rf"\b{old}\b", nv, head)
            h = re.sub(rf"\btheorem\s+{name}\b", f"theorem {name}_{nv}", h)
            variants.append(f"{h} := by {tac}")
        # Lean-check all variants in PARALLEL across the cores (was a serial loop).
        from verifiers import verify_many
        for variant, r in zip(variants, verify_many([("lean", v) for v in variants])):
            if getattr(r, "passed", False):
                out.append(variant)
    return out


def tactic_logit_bias(model_path, tactics=("omega", "simp", "decide", "tauto"), boost=8):
    """Build an OpenAI-style logit_bias {token_id: boost} for the FIRST token of each closing tactic, so the
    server biases the model toward TRYING them on stuck goals (the deep-MLX inference complement to
    enumerate_tactics). Loads only the tokenizer (GPU-free). No-op if the server ignores logit_bias."""
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_path)
    bias = {}
    for tac in tactics:
        for variant in (" " + tac, tac, " by " + tac):
            ids = tok.encode(variant, add_special_tokens=False)
            if ids:
                bias[str(ids[0])] = boost
    return bias


def goal_is_arithmetic(stmt):
    """Only bias toward omega/simp for ARITHMETIC goals — biasing them on LOGIC goals (∧∨→, which need
    term-mode/tauto) BREAKS proofs (MEASURED: naive bias 4/5→3/5, and_comm regressed). This conditioning fixes it."""
    goal = stmt.split(":")[-1]
    if any(c in goal for c in ("∧", "∨", "→", "↔", "¬")):
        return False
    return any(op in goal for op in ("+", "-", "*", "≤", "<", "≥", ">"))


_PREMISE_IDX = None


def inject_premises(stmt, k=8):
    """Premise selection (the #1 lever: 4%→20%, LeanSearch v2). Prepend retrieved relevant mathlib lemmas to
    the goal so the model knows which to use. Lazy-builds the BM25 index once (parse mathlib, ~1-2 min)."""
    global _PREMISE_IDX
    if _PREMISE_IDX is None:
        sys.path.insert(0, os.path.join(HERE, "..", "src"))
        from premise_select import PremiseIndex, build_corpus
        _PREMISE_IDX = PremiseIndex(build_corpus())
    names = _PREMISE_IDX.retrieve(stmt, k)
    return f"Relevant mathlib lemmas (consider using): {', '.join(names)}\n\nProve this theorem:\n{stmt}"


def chat(base_url, model, msgs, max_tokens=700, logit_bias=None):
    body = {"model": model, "messages": msgs, "temperature": 0.4, "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False}}
    if logit_bias:
        body["logit_bias"] = logit_bias                  # deep-MLX: steer decode toward closing tactics
    data = json.dumps(body).encode()
    import time as _t
    for attempt in range(4):                             # retry transient server hiccups (RemoteDisconnected/timeout)
        try:
            req = urllib.request.Request(base_url + "/chat/completions", data, {"Content-Type": "application/json"})
            m = json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]
            return m.get("content") or m.get("reasoning") or ""
        except Exception:  # noqa: BLE001
            if attempt == 3:
                raise
            _t.sleep(2 * (attempt + 1))
    return ""


def extract(text, stmt):
    m = re.search(r"```lean\s*\n(.*?)```", text, re.S) or re.search(r"(theorem .*)", text, re.S)
    p = (m.group(1) if m else text).strip()
    if "theorem" not in p:
        p = stmt + " := by " + p.lstrip(":= by ").strip()
    return p


def extract_goals(diag):
    """Pull the remaining proof STATE from Lean's 'unsolved goals' output. Research (BFS-Prover; LeanProgress,
    arXiv 2502.17925) shows tactic-state feedback guides self-correction far better than a raw error dump — the
    model sees what's LEFT to prove (⊢ …), not just that it failed. Pure parse (no Lean); '' if none found."""
    m = re.search(r"unsolved goals\s*\n(.*?)(?:\n\nerror|\Z)", diag, re.S)
    if m:
        return m.group(1).strip()[:400]
    m = re.search(r"(⊢ .+?)(?:\n\n|\Z)", diag, re.S)              # bare turnstile goal
    return m.group(1).strip()[:400] if m else ""


def prove_one(base_url, model, stmt, attempts=3, correct=2, enumerate_fallback=False, logit_bias=None,
              premises=False):
    """Best-of-N attempts, each with K rounds of verifier-guided self-correction (feed the Lean error).
    enumerate_fallback=True (GEN/training only, NEVER the honest eval): if the model fails all attempts,
    brute-force CORE_TACTICS to bootstrap a verified proof — the cold-start plateau breaker.
    premises=True: prepend retrieved mathlib lemmas to the goal (premise selection, the 4%→20% lever)."""
    last = ""
    user = inject_premises(stmt) if premises else stmt
    for _ in range(attempts):
        msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": user}]
        for _ in range(correct + 1):
            last = extract(chat(base_url, model, msgs, logit_bias=logit_bias), stmt)
            r = verify_lean(last)
            if getattr(r, "passed", False):
                msgs.append({"role": "assistant", "content": f"```lean\n{last}\n```"})
                return True, last, msgs            # msgs = the full trajectory (incl. self-corrections)
            diag = getattr(r, "diag", "") or ""
            goals = extract_goals(diag)                  # research-backed: lead with the REMAINING goal, not just the error
            state = f"Lean still needs these goal(s) closed:\n{goals}\n\n" if goals else ""
            msgs += [{"role": "assistant", "content": f"```lean\n{last}\n```"},
                     {"role": "user", "content": f"That failed. {state}Lean error:\n{diag[:400]}\nFix it — output ONLY the corrected ```lean block."}]
    if enumerate_fallback:                          # cold-start bootstrap: brute-force tactics → verified proof to train on
        proof = enumerate_tactics(stmt)
        if proof:
            return True, proof, [{"role": "system", "content": SYS}, {"role": "user", "content": stmt},
                                 {"role": "assistant", "content": f"```lean\n{proof}\n```"}]
    return False, last, msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--correct", type=int, default=2)
    ap.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v4")
    ap.add_argument("--logit-bias", action="store_true", help="boost closing-tactic tokens (deep-MLX inference plateau-breaker)")
    ap.add_argument("--premises", action="store_true", help="prepend retrieved mathlib lemmas (premise selection, 4%→20%)")
    args = ap.parse_args()
    os.environ["PATH"] = os.path.expanduser("~/.elan/bin") + os.pathsep + os.environ.get("PATH", "")

    full_bias = tactic_logit_bias(args.model) if args.logit_bias else None
    passed = 0
    for stmt in SMOKE[:args.n]:
        lb = full_bias if (full_bias and goal_is_arithmetic(stmt)) else None   # bias ONLY arithmetic goals
        ok, proof, _ = prove_one(args.base_url, args.model, stmt, args.attempts, args.correct,
                                 logit_bias=lb, premises=args.premises)
        passed += int(ok)
        print(f"  {'✓' if ok else '✗'} {stmt[:46]:48s}{'  ' + proof.splitlines()[-1][:30] if ok else ''}",
              flush=True)
    n = min(args.n, len(SMOKE))
    print(f"\n  FORMAL-MATH: {passed}/{n} Lean-verified  (best-of-{args.attempts} + {args.correct}-round self-correct)")


if __name__ == "__main__":
    main()
