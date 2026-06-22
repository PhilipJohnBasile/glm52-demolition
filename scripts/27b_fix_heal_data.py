#!/usr/bin/env python3
"""Fix + augment heal/data WITHOUT re-pulling HF (fast, offline):
  (1) merge callsieve-protocol trajectories (the token-saving reflex), weighted;
  (2) FILTER the NaN root cause: drop rows whose PROMPT alone >= max_seq, because
      --mask-prompt then leaves zero completion tokens after truncation -> loss
      0/0 = NaN at iter-1 val (the bug that burned two heal runs);
  (3) reshuffle + resplit train/valid.

Tokenizer-only (no 99 GB weight load).

  python scripts/27b_fix_heal_data.py --max-seq 768 --cs-weight 3
"""
import argparse
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")


def load_jsonl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def last_assistant_idx(msgs):
    for i in range(len(msgs) - 1, -1, -1):
        if msgs[i].get("role") == "assistant" and str(msgs[i].get("content", "")).strip():
            return i
    return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--max-seq", type=int, default=768)
    ap.add_argument("--cs-weight", type=int, default=3)
    args = ap.parse_args()
    import random
    random.seed(0)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(ROOT, args.model),
                                        trust_remote_code=True)

    data_dir = os.path.join(ROOT, "heal", "data")
    rows = load_jsonl(os.path.join(data_dir, "train.jsonl")) + \
        load_jsonl(os.path.join(data_dir, "valid.jsonl"))
    cs = load_jsonl(os.path.join(ROOT, "heal", "mine", "callsieve_protocol.jsonl"))
    rows += cs * args.cs_weight
    print(f"  in: {len(rows)} rows (incl callsieve x{args.cs_weight} = {len(cs)*args.cs_weight})")

    keep, drop_nan, drop_bad = [], 0, 0
    margin = 8
    for r in rows:
        msgs = r.get("messages")
        if not isinstance(msgs, list) or len(msgs) < 2:
            drop_bad += 1
            continue
        idx = last_assistant_idx(msgs)
        if idx <= 0:
            drop_bad += 1
            continue
        try:
            plen = len(tok.apply_chat_template(msgs[:idx], add_generation_prompt=True,
                                               tokenize=True))
        except Exception:  # noqa: BLE001
            # fallback: char heuristic (~3 chars/token)
            plen = sum(len(str(m.get("content", ""))) for m in msgs[:idx]) // 3
        if plen >= args.max_seq - margin:        # the NaN cause
            drop_nan += 1
            continue
        keep.append(r)

    random.shuffle(keep)
    nv = max(50, len(keep) // 40)
    for name, d in [("valid", keep[:nv]), ("train", keep[nv:])]:
        with open(os.path.join(data_dir, f"{name}.jsonl"), "w") as f:
            f.write("\n".join(json.dumps(x) for x in d))
    print(f"  dropped: {drop_nan} prompt>=max_seq (NaN cause), {drop_bad} malformed")
    print(f"  out: {len(keep)-nv} train / {nv} valid  (all prompts < {args.max_seq} tokens)")


if __name__ == "__main__":
    main()
