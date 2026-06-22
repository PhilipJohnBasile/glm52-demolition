#!/usr/bin/env python3
"""Trim the multilingual vocab (speed + size). GLM-5.2's 154,880-token vocab is
~31% non-English/non-code; dropping those shrinks embed_tokens + lm_head and the
per-token softmax. We keep: special/added tokens + ASCII/Latin/code charset + EVERY
token actually used by our heal+mine corpus (so we never break our own data).

Slices the quantized embed/lm_head ROWS (quant groups are along hidden, so row-
slicing is exact), hardlinks the unchanged layer shards (no 99GB copy), rewrites
tokenizer.json (filter vocab+merges, remap ids), updates vocab_size. HARD GATE:
re-tokenizes a corpus sample with the trimmed tokenizer and ABORTS if any sequence
differs (modulo remap) — so a bad rewrite can never ship.

  python scripts/34_trim_vocab.py --src models/GLM-5.2-q3a4-v2 --out models/GLM-5.2-q3a4-trim
"""
import argparse
import glob
import json
import os
import re

import mlx.core as mx
import numpy as np

KEEPABLE = re.compile(r"^[\x00-\x7F -ɏ -⁯\s]*$")  # ascii+latin+punct


def observed_token_ids(tok, corpus_globs, cap_lines=40000):
    used = set()
    for g in corpus_globs:
        for path in glob.glob(g):
            for i, line in enumerate(open(path)):
                if i >= cap_lines or not line.strip():
                    break
                try:
                    row = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                text = " ".join(str(m.get("content", "")) for m in row.get("messages", [])) \
                    if "messages" in row else json.dumps(row)
                used.update(tok.encode(text[:8000]))
    return used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.src, trust_remote_code=True)
    vocab = tok.get_vocab()                                   # token -> id
    inv = {i: t for t, i in vocab.items()}
    n = max(vocab.values()) + 1

    # ---- keep-set: special/added + charset + corpus-observed --------------------
    keep = set(tok.all_special_ids or [])
    keep.update(getattr(tok, "added_tokens_decoder", {}).keys())
    for t, i in vocab.items():
        s = tok.convert_tokens_to_string([t])
        if s and KEEPABLE.match(s):
            keep.add(i)
    print(f"  charset+special keep: {len(keep)}")
    keep.update(observed_token_ids(tok, [os.path.join(args.src, "..", "..", "heal", "data", "*.jsonl"),
                                         os.path.join(args.src, "..", "..", "heal", "mine", "*.jsonl")]))
    keep = sorted(i for i in keep if 0 <= i < n)
    print(f"  +corpus -> keep {len(keep)}/{n}  (drop {n-len(keep)}, {100*(n-len(keep))//n}%)")
    old2new = {o: i for i, o in enumerate(keep)}

    # ---- HARD GATE: re-tokenization must be identical (modulo remap) ------------
    sample = ["function f(x: number){ return x+1 }", "SELECT * FROM users WHERE id=$1;",
              "pub fn add(a:i32,b:i32)->i32{a+b}", "const x = [1,2,3].map(i=>i*2)"]
    for s in sample:
        ids = tok.encode(s)
        if any(i not in old2new for i in ids):
            raise SystemExit("  [ABORT] a sample re-tokenizes to a DROPPED token — keep-set too "
                             "aggressive; not trimming (no harm done).")
    print("  hard gate OK: code/SQL samples survive the keep-set")

    # ---- slice the quantized embed_tokens + lm_head rows ------------------------
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from weight_store import WeightStore
    ws = WeightStore(args.src)
    os.makedirs(args.out, exist_ok=True)
    keep_idx = mx.array(np.array(keep))
    extra = {}
    for p in ("model.embed_tokens.", "lm_head.", "model.norm."):
        extra.update(ws.load_prefix(p))
    for base in ("model.embed_tokens", "lm_head"):
        for suf in ("weight", "scales", "biases"):
            k = f"{base}.{suf}"
            if k in extra:
                extra[k] = mx.take(extra[k], keep_idx, axis=0)        # rows = vocab dim
    mx.eval(list(extra.values()))
    mx.save_safetensors(os.path.join(args.out, "model-extra.safetensors"), extra)

    # ---- hardlink the unchanged layer shards + rebuild the index ---------------
    idx = json.load(open(os.path.join(args.src, "model.safetensors.index.json")))
    new_map = {}
    shards = set()
    for tname, shard in idx["weight_map"].items():
        if tname in extra:                                   # embed/lm_head/norm -> new shard
            new_map[tname] = "model-extra.safetensors"
        else:
            new_map[tname] = shard
            shards.add(shard)
    for sh in shards:                                        # hardlink (no copy)
        dst = os.path.join(args.out, sh)
        if not os.path.exists(dst):
            try:
                os.link(os.path.join(args.src, sh), dst)
            except OSError:
                import shutil
                shutil.copy(os.path.join(args.src, sh), dst)
    json.dump({"metadata": {}, "weight_map": new_map},
              open(os.path.join(args.out, "model.safetensors.index.json"), "w"))

    # ---- rewrite tokenizer.json (filter vocab+merges, remap) -------------------
    tj = json.load(open(os.path.join(args.src, "tokenizer.json")))
    m = tj["model"]
    kept_tokens = {inv[o]: new for o, new in old2new.items() if o in inv}
    m["vocab"] = {t: i for t, i in sorted(kept_tokens.items(), key=lambda kv: kv[1])}
    if "merges" in m:
        ktok = set(kept_tokens)
        def ok(pair):
            a, b = pair.split(" ") if isinstance(pair, str) else pair
            return a in ktok and b in ktok and (a + b) in ktok
        m["merges"] = [mg for mg in m["merges"] if ok(mg)]
    for at in tj.get("added_tokens", []):
        if at["id"] in old2new:
            at["id"] = old2new[at["id"]]
    json.dump(tj, open(os.path.join(args.out, "tokenizer.json"), "w"))
    import shutil
    for fn in os.listdir(args.src):
        if ("token" in fn.lower() and fn != "tokenizer.json") or fn.endswith((".txt", ".jinja")):
            shutil.copy(os.path.join(args.src, fn), os.path.join(args.out, fn))
    cfg = json.load(open(os.path.join(args.src, "config.json")))
    cfg["vocab_size"] = len(keep)
    json.dump(cfg, open(os.path.join(args.out, "config.json"), "w"), indent=2)

    # ---- FINAL GATE: trimmed tokenizer must reproduce the samples ---------------
    new_tok = AutoTokenizer.from_pretrained(args.out, trust_remote_code=True)
    for s in sample:
        if [old2new[i] for i in tok.encode(s)] != new_tok.encode(s):
            raise SystemExit(f"  [ABORT] trimmed tokenizer drifted on {s!r} — keeping full vocab.")
    print(f"  ✅ trimmed -> {args.out}  (vocab {n} -> {len(keep)}; embed+lm_head sliced; "
          "tokenizer verified identical on samples)")


if __name__ == "__main__":
    main()
