#!/usr/bin/env python3
"""PhD-math Phase 2 (#28) — Lean EXPERT ITERATION = the self-heal flywheel pointed at Lean.

Generate proofs for a batch of theorems (best-of-N + verifier-guided self-correction, via 66_prove),
keep the LEAN-VERIFIED ones, write them as SFT data → 06_heal_lora SFTs adapters-lean-v2 → the model
INTERNALIZES the tactics → pass@1 climbs. Goedel-Prover's recipe, local + MLX-bounded. No human labels —
the Lean compiler is the supervision.

  python scripts/67_lean_expert.py gen --base-url http://127.0.0.1:8080/v1 --model models/GLM-5.2-q3a4-v4
"""
import argparse
import importlib.util
import json
import os
import re

HERE = os.path.dirname(__file__)
_spec = importlib.util.spec_from_file_location("p66", os.path.join(HERE, "66_prove.py"))
p66 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p66)

# the expert-iteration pool: simple→moderate theorems provable with core tactics (omega/simp/rfl/term-mode).
# The model proves what it can; the VERIFIED ones become training data so it learns the tactics natively.
THEOREMS = [
    "theorem t1 (n : Nat) : n = n",
    "theorem t2 : 1 + 1 = 2",
    "theorem t3 (n : Nat) : 0 + n = n",
    "theorem t4 (a b : Nat) : a + b = b + a",
    "theorem t5 (p q : Prop) (h : p ∧ q) : q ∧ p",
    "theorem t6 (n : Nat) : n + 0 = n",
    "theorem t7 (a b c : Nat) : a + b + c = a + (b + c)",
    "theorem t8 (n : Nat) : n * 1 = n",
    "theorem t9 (n : Nat) : 1 * n = n",
    "theorem t10 (n : Nat) : n * 0 = 0",
    "theorem t11 (p q : Prop) (h : p ∨ q) : q ∨ p",
    "theorem t12 (p : Prop) (h : p) : p ∨ p",
    "theorem t13 (n : Nat) : n ≤ n",
    "theorem t14 (n : Nat) : n < n + 1",
    "theorem t15 (a b : Nat) (h : a = b) : b = a",
    "theorem t16 (p q r : Prop) (h1 : p) (h2 : q) (h3 : r) : p ∧ q ∧ r",
    "theorem t17 (a b : Nat) : a * b = b * a",
    "theorem t18 (n : Nat) : 2 * n = n + n",
    "theorem t19 (a b : Nat) : a + b - b = a",
    "theorem t20 (p q : Prop) (h : p → q) (hp : p) : q",
]


DECOMP = ("This Lean 4 theorem is hard. Break it into 2-3 SIMPLER helper lemmas — the building blocks that "
          "would make it easy. Output each as a complete Lean 4 theorem STATEMENT (`theorem name ... : ...`, "
          "NO proof), one per line, in a ```lean code block.")

CONJECTURE = ("Propose {n} NEW Lean 4 theorem STATEMENTS about natural numbers / lists / logic that are TRUE "
              "and provable with basic tactics (omega, simp, rfl, term-mode, induction), but slightly HARDER "
              "or more varied than these:\n{examples}\n\nOutput each as a complete `theorem name ... : ...` "
              "(NO proof), one per line, in a ```lean block. Make them genuinely novel, not copies.")


def conjecture(base_url, model, out_dir, n=10):
    """STP self-play (plateau lever #1, the BIG one): the model proposes NOVEL theorems 'just beyond' its
    current set → an infinite fresh curriculum (vs a fixed 20-pool). Lean-validate each statement, append the
    well-formed ones to curriculum.jsonl for the next gen round. The conjecturer role of conjecturer↔prover."""
    os.makedirs(out_dir, exist_ok=True)
    examples = "\n".join(THEOREMS[:6])
    try:
        out = p66.chat(base_url, model, [{"role": "user", "content": CONJECTURE.format(n=n, examples=examples)}])
    except Exception:  # noqa: BLE001
        return []
    block = re.search(r"```lean\s*\n(.*?)```", out, re.S)
    proposed = []
    for line in (block.group(1) if block else out).splitlines():
        line = line.strip()
        if line.startswith("theorem") and ":" in line:
            ok, head = valid_statement(line)
            if ok and head not in THEOREMS:
                proposed.append(head)
    proposed = list(dict.fromkeys(proposed))
    cpath = os.path.join(out_dir, "curriculum.jsonl")
    existing = set()
    if os.path.exists(cpath):
        for line in open(cpath):
            try:
                existing.add(json.loads(line).get("theorem", "").strip())
            except Exception:  # noqa: BLE001
                pass
    with open(cpath, "a") as f:
        for s in proposed:
            if s not in existing:
                f.write(json.dumps({"theorem": s}) + "\n")
    print(f"  CONJECTURE (STP self-play): model proposed {len(proposed)} novel Lean-valid theorems → {cpath}")
    print("  (the conjecturer feeds the prover — fresh curriculum each round, the BIG plateau-breaker)")
    return proposed


def valid_statement(stmt):
    """Is `stmt` a well-formed Lean theorem statement? It compiles with `:= by sorry` (sorry = a WARNING,
    not an error; a malformed statement is a parse/type ERROR). Returns (ok, the bare statement head)."""
    head = stmt.split(":=")[0].strip()
    return getattr(p66.verify_lean(head + " := by sorry"), "passed", False), head


def scaffold(base_url, model, failed_theorems, out_dir):
    """Scaffolded data synthesis (Goedel's #1 lever, how it scales to miniF2F): each FAILED theorem → the
    model decomposes it into easier sub-lemmas → Lean validates each statement → emit an EASY→HARD
    curriculum (`curriculum.jsonl`) to feed as the NEXT round's theorems. Failures become a ladder."""
    curriculum = []
    for stmt in failed_theorems:
        try:
            out = p66.chat(base_url, model, [{"role": "user", "content": DECOMP + "\n\n" + stmt}])
        except Exception:  # noqa: BLE001
            continue
        block = re.search(r"```lean\s*\n(.*?)```", out, re.S)
        for line in (block.group(1) if block else out).splitlines():
            line = line.strip()
            if line.startswith("theorem") and ":" in line:
                ok, head = valid_statement(line)
                if ok:
                    curriculum.append(head)
    curriculum = list(dict.fromkeys(curriculum))          # dedup, keep order
    path = os.path.join(out_dir, "curriculum.jsonl")
    with open(path, "w") as f:
        for s in curriculum:
            f.write(json.dumps({"theorem": s}) + "\n")
    print(f"  SCAFFOLD: {len(failed_theorems)} failed → {len(curriculum)} valid easier sub-lemmas → {path}")
    print("  (feed curriculum.jsonl as the next round's theorems — easy→hard, the Goedel scaling lever)")
    return curriculum


def gen(base_url, model, out_dir, attempts=4, correct=3):
    os.makedirs(out_dir, exist_ok=True)
    # plateau-breaker (lever #2): feed last round's scaffold curriculum forward — the self-evolving
    # easy→hard curriculum that gives expert-iteration headroom past saturation.
    theorems = list(THEOREMS)
    cpath = os.path.join(out_dir, "curriculum.jsonl")
    if os.path.exists(cpath):
        for line in open(cpath):
            try:
                t = json.loads(line).get("theorem", "").strip()
                if t and t not in theorems:
                    theorems.append(t)
            except Exception:  # noqa: BLE001
                pass
    data, failed, n_verified, n_traj = [], [], 0, 0
    for stmt in theorems:
        ok, proof, traj = p66.prove_one(base_url, model, stmt, attempts, correct, enumerate_fallback=True)
        corrected = ok and len(traj) > 3                 # >3 msgs ⇒ a failed→error→fixed self-correction happened
        print(f"  {'✓' if ok else '✗'} {stmt[:52]}{'  (self-corrected → trajectory saved)' if corrected else ''}",
              flush=True)
        if ok:
            n_verified += 1
            data.append({"messages": [
                {"role": "user", "content": f"Prove this Lean 4 theorem:\n{stmt}"},
                {"role": "assistant", "content": f"```lean\n{proof}\n```"}]})
            if corrected:                                # SAVE the trajectory → the model learns to self-correct NATIVELY
                n_traj += 1
                data.append({"messages": traj})
        else:
            failed.append(stmt)                          # failures feed the scaffold curriculum
    train = os.path.join(out_dir, "train.jsonl")
    with open(train, "w") as f:
        for r in data:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(out_dir, "valid.jsonl"), "w") as f:
        for r in data[:max(1, len(data) // 8)]:
            f.write(json.dumps(r) + "\n")
    print(f"\n  PHASE 2 GEN: {n_verified}/{len(theorems)} theorems Lean-verified "
          f"(+{n_traj} self-correction trajectories) → {len(data)} training rows → {train}")
    if failed:
        scaffold(base_url, model, failed, out_dir)       # failures → easy→hard curriculum for the next round
    print("  next: SFT 06_heal_lora --data heal/lean-combined → adapters-lean-v2, then re-eval pass@1")
    return n_verified


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["gen", "conjecture"])
    ap.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v4")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "heal", "lean-rft"))
    ap.add_argument("--attempts", type=int, default=4)
    ap.add_argument("--correct", type=int, default=3)
    args = ap.parse_args()
    os.environ["PATH"] = os.path.expanduser("~/.elan/bin") + os.pathsep + os.environ.get("PATH", "")
    if args.mode == "gen":
        gen(args.base_url, args.model, args.out, args.attempts, args.correct)
    elif args.mode == "conjecture":
        conjecture(args.base_url, args.model, args.out)


if __name__ == "__main__":
    main()
