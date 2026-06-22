#!/usr/bin/env python3
"""Build the v4 REAP calibration set — BALANCED across math, science, code, design,
reasoning. The v3 calibration was pure code (heal/mine/verified.jsonl), so the saliency
never saw math and the math 'super-experts' scored low and got pruned -> math collapse
(0/5 GSM8K, the known super-expert failure mode). Feeding REAP a balanced mix makes those
experts light up and survive the cut. Output feeds scripts/23_stream_calibrate.py.

  python scripts/61_build_calib_v4.py --per 45 --out calib/calib_v4.jsonl
"""
import argparse
import json
import os
import random

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")


def _sample_jsonl(path, k, to_text):
    if not os.path.exists(path):
        return []
    rows = [json.loads(l) for l in open(path) if l.strip()]
    random.shuffle(rows)
    out = []
    for r in rows:
        t = to_text(r)
        if t and len(t) > 80:
            out.append(t)
        if len(out) >= k:
            break
    return out


def math_texts(k):
    out = []
    try:
        from datasets import load_dataset
        g = load_dataset("openai/gsm8k", "main", split="train")
        for i in random.sample(range(len(g)), min(k, len(g))):
            out.append(f"Problem: {g[i]['question']}\nSolution: {g[i]['answer']}")
    except Exception as e:  # noqa: BLE001
        print(f"  gsm8k skip: {str(e)[:50]}")
    try:                                                     # competition math + R1 long-CoT traces
        from datasets import load_dataset
        r = load_dataset("open-r1/OpenR1-Math-220k", "default", split="train", streaming=True)
        for i, ex in enumerate(r):
            if i >= k:
                break
            sol = (ex.get("generations") or [""])[0] if isinstance(ex.get("generations"), list) else ex.get("solution", "")
            out.append(f"Problem: {ex.get('problem', '')}\nSolution: {str(sol)[:3000]}")
    except Exception as e:  # noqa: BLE001
        print(f"  OpenR1-Math skip: {str(e)[:50]}")
    return out[: 2 * k]


def science_texts(k):
    import sys
    sys.path.insert(0, os.path.join(ROOT, "src"))
    out = []
    try:
        from sci_tools import arxiv_search
        for q in ["transformer attention", "diffusion models", "protein folding",
                  "quantum error correction", "reinforcement learning"]:
            r = arxiv_search(q, k=max(2, k // 5))
            out += [b.strip() for b in r.split("\n- ") if len(b.strip()) > 120]
    except Exception as e:  # noqa: BLE001
        print(f"  arxiv skip: {str(e)[:50]}")
    return out[:k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=45, help="target sequences per domain")
    ap.add_argument("--out", default=os.path.join(ROOT, "calib", "calib_v4.jsonl"))
    args = ap.parse_args()
    random.seed(0)
    code_to_text = (lambda r: "\n".join(m.get("content", "") for m in r.get("messages", []))
                    if "messages" in r else r.get("text", ""))
    buckets = {
        # code is the PRIMARY niche -> lead with it so the code super-experts survive,
        # while math/science get enough representation to keep THEIR experts too.
        "code": _sample_jsonl(os.path.join(ROOT, "heal", "mine", "verified.jsonl"), 2 * args.per,
                              code_to_text),
        "math": math_texts(args.per)[: args.per + args.per // 3],
        "science": science_texts(args.per // 2),
        "design": _sample_jsonl(os.path.join(ROOT, "heal", "mine", "design.jsonl"), args.per // 2,
                                code_to_text),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    n = 0
    with open(args.out, "w") as f:
        for dom, texts in buckets.items():
            for t in texts:
                f.write(json.dumps({"text": t[:6000], "domain": dom}) + "\n")
                n += 1
            print(f"  {dom:8} {len(texts)}")
    print(f"\n  v4 calibration -> {args.out}  ({n} balanced sequences)")
    print("  next: scripts/23_stream_calibrate.py --model models/GLM-5.2-mxfp4 "
          f"--data {args.out} --n {n} --out models/saliency_v4.npz")


if __name__ == "__main__":
    main()
