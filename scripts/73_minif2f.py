#!/usr/bin/env python3
"""#31 — the FULL miniF2F formal-math benchmark. Downloads miniF2F (Lean 4) + runs 66_prove (best-of-N +
verifier-guided self-correction) over each problem → pass@N, every proof Lean-verified. The publishable
number (honest: miniF2F is AIME/IMO/AMC-hard; a 99GB pruned model with basic-Lean heal will score low —
that's fine, it's a real number). Harness GPU-free; the eval runs on the GPU (hours for 244 problems).

  python scripts/73_minif2f.py --split test --n 244 --attempts 4 --correct 2
"""
import argparse
import importlib.util
import json
import os

HERE = os.path.dirname(__file__)
_spec = importlib.util.spec_from_file_location("p66", os.path.join(HERE, "66_prove.py"))
p66 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p66)

DATASETS = ["cat-searcher/minif2f-lean4", "brando/minif2f-lean4", "HaimingW/miniF2F-lean4",
            "internlm/miniF2F-lean4"]


def load_problems(split, limit):
    from datasets import load_dataset
    ds, last = None, None
    for name in DATASETS:
        try:
            ds = load_dataset(name, split=split)
            print(f"  loaded {name} [{split}]")
            break
        except Exception as e:  # noqa: BLE001
            last = e
    if ds is None:
        raise RuntimeError(f"no miniF2F dataset loaded; last error: {last}")
    probs = []
    for row in ds:
        stmt = (row.get("formal_statement") or row.get("statement") or row.get("lean4")
                or row.get("informal_statement") or "").strip()
        if stmt.startswith(("theorem", "lemma")):
            probs.append(stmt.split(":=")[0].strip())   # statement head; 66_prove generates the proof
        if len(probs) >= limit:
            break
    return probs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    ap.add_argument("--n", type=int, default=244)
    ap.add_argument("--attempts", type=int, default=4)
    ap.add_argument("--correct", type=int, default=2)
    ap.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v4")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "logs", "minif2f_results.jsonl"))
    ap.add_argument("--premises", action="store_true", help="semantic premise selection (the 4%→20% lever)")
    args = ap.parse_args()
    os.environ["PATH"] = os.path.expanduser("~/.elan/bin") + os.pathsep + os.environ.get("PATH", "")
    probs = load_problems(args.split, args.n)
    print(f"  miniF2F-{args.split}: {len(probs)} problems, best-of-{args.attempts} + {args.correct}-round self-correct")
    solved = 0
    with open(args.out, "w") as f:
        for i, stmt in enumerate(probs, 1):
            ok, proof, _ = p66.prove_one(args.base_url, args.model, stmt, args.attempts, args.correct,
                                         premises=args.premises)
            solved += bool(ok)
            f.write(json.dumps({"stmt": stmt, "ok": bool(ok), "proof": proof if ok else None}) + "\n")
            print(f"  [{i}/{len(probs)}] {'✓' if ok else '✗'} {stmt[:58]}  (running {solved}/{i})", flush=True)
    pct = 100 * solved / max(len(probs), 1)
    print(f"\n  MINIF2F-{args.split.upper()}: {solved}/{len(probs)} = {pct:.1f}% Lean-verified (pass@{args.attempts}) -> {args.out}")


if __name__ == "__main__":
    main()
