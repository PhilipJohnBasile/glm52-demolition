#!/usr/bin/env python3
"""Heal the pruned+quantized GLM-5.2 with (Q)LoRA so it recovers as much of the
flagship's behavior as possible on your 7-language agentic stack.

Pruning deletes ~60% of experts; the router still points at the survivors but
the *balance* the model was trained with is gone. A short LoRA pass re-tunes the
surviving experts + attention to compensate. This is the single biggest quality
lever after calibration.

Two data modes:

  --mode distill   (BEST) Use the real flagship GLM-5.2 as TEACHER via Z.ai's
                   API: send coding/agentic prompts, collect the flagship's
                   answers, train the local pruned model to imitate them. This
                   transfers actual flagship behavior into your local model.
                   Needs ZAI_API_KEY. We cannot run the 395GB teacher locally,
                   so the API is the only way to distill from the real thing.

  --mode sft       (FREE/LOCAL) Train on ground-truth coding + tool-calling
                   datasets filtered/weighted to your languages. No teacher, no
                   API; recovers task ability but not flagship style.

Both write heal/data/{train,valid}.jsonl in MLX-LM chat format, then run
`mlx_lm.lora`. Loss is masked to assistant tokens only (--mask-prompt) so we
train on completions, not prompts.

Serve afterward with the adapter:
  mlx_lm.server --model models/GLM-5.2-demolished-mxmix \
                --adapter-path heal/adapters
(or fuse with scripts note below).
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")

# English-only: keep the heal distribution consistent with the English-only
# prune so we don't re-teach pruned-away Chinese/other-script capability.
_FOREIGN = [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x3040, 0x30FF),
            (0xAC00, 0xD7AF), (0x0400, 0x04FF), (0x0600, 0x06FF), (0x0590, 0x05FF)]


def is_english(text, max_foreign=0.02):
    if not text:
        return False
    foreign = letters = 0
    for c in str(text):
        if c.isalpha():
            letters += 1
            o = ord(c)
            if any(lo <= o <= hi for lo, hi in _FOREIGN):
                foreign += 1
    return letters == 0 or foreign / letters <= max_foreign


def english_pair(row):
    """True if every message in a chat row is English."""
    return all(is_english(m.get("content", "")) for m in row.get("messages", []))
DATA_DIR = os.path.join(ROOT, "heal", "data")
ADAPTER_DIR = os.path.join(ROOT, "heal", "adapters")
CONFIG = os.path.join(ROOT, "heal", "lora_config.yaml")

# Per-language prompt mix for the heal set — mirrors calibration weighting so we
# heal hardest where the model is weakest (Rust) and on first-class UI (HTML/CSS).
LANG_PROMPT_WEIGHTS = {
    "python": 1.0, "typescript": 0.8, "javascript": 0.5, "go": 0.9,
    "rust": 1.2, "html": 0.9, "css": 0.9,
}
SFT_DATASETS = [
    "theblackcat102/evol-codealpaca-v1",      # instruction->code
    "Salesforce/xlam-function-calling-60k",   # tool-calling / agentic
]


# ---------- prompt sourcing (shared by both modes) ----------
def gather_prompts(n_per_lang):
    """Collect coding/agentic instruction prompts, language-tagged."""
    prompts = []
    try:
        from datasets import load_dataset
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] datasets unavailable ({e}); using built-in seed prompts")
        load_dataset = None

    if load_dataset:
        try:
            ds = load_dataset(SFT_DATASETS[0], split="train", streaming=True)
            for ex in ds:
                instr = ex.get("instruction", "")
                if instr.strip():
                    prompts.append({"prompt": instr, "lang": "mixed"})
                if len(prompts) >= n_per_lang * len(LANG_PROMPT_WEIGHTS):
                    break
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] prompt source failed: {e}")

    # language-targeted synthetic prompts to guarantee coverage of weak langs
    templates = {
        "rust": "In Rust, {t}. Use idiomatic error handling.",
        "go": "In Go, {t}. Follow standard library idioms.",
        "html": "Write semantic, accessible HTML for {t}.",
        "css": "Write modern responsive CSS (grid/flexbox) for {t}.",
        "typescript": "In strict TypeScript, {t}.",
        "python": "In Python, {t}. Include type hints.",
        "javascript": "In modern JavaScript, {t}.",
    }
    tasks = ["a function to parse and validate user input",
             "a small module with unit tests",
             "an agent tool that reads a file and returns a summary",
             "a responsive card component", "a retry-with-backoff helper",
             "a CLI that takes args and prints JSON"]
    for lang, w in LANG_PROMPT_WEIGHTS.items():
        tmpl = templates.get(lang)
        if not tmpl:
            continue
        for i in range(max(1, int(n_per_lang * w))):
            prompts.append({"prompt": tmpl.format(t=tasks[i % len(tasks)]),
                            "lang": lang})
    return prompts


# ---------- mode: distill from flagship via Z.ai API ----------
def zai_chat(prompt, model, api_key, base_url):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2, "max_tokens": 1200,
    }).encode()
    req = urllib.request.Request(
        f"{base_url}/chat/completions", body,
        {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def build_distill(prompts, args):
    key = os.environ.get("ZAI_API_KEY")
    if not key:
        sys.exit("  [stop] --mode distill needs ZAI_API_KEY (the flagship "
                 "teacher). Get one from z.ai, or use --mode sft.")
    rows = []
    for i, p in enumerate(prompts):
        try:
            ans = zai_chat(p["prompt"], args.teacher_model, key, args.teacher_url)
        except Exception as e:  # noqa: BLE001
            print(f"  [skip] teacher call {i} failed: {str(e)[:60]}")
            continue
        rows.append({"messages": [
            {"role": "user", "content": p["prompt"]},
            {"role": "assistant", "content": ans}]})
        if (i + 1) % 25 == 0:
            print(f"  distilled {i + 1}/{len(prompts)} from flagship")
        time.sleep(args.sleep)
    return rows


# ---------- mode: SFT from ground-truth datasets ----------
def build_sft(args):
    rows = []
    try:
        from datasets import load_dataset
    except Exception as e:  # noqa: BLE001
        sys.exit(f"  [stop] --mode sft needs `datasets` ({e})")
    # instruction->code pairs
    try:
        ds = load_dataset(SFT_DATASETS[0], split="train", streaming=True)
        for i, ex in enumerate(ds):
            if i >= args.n:
                break
            u, a = ex.get("instruction", ""), ex.get("output", "")
            if u.strip() and a.strip():
                rows.append({"messages": [
                    {"role": "user", "content": u},
                    {"role": "assistant", "content": a}]})
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] {SFT_DATASETS[0]} failed: {e}")
    # tool-calling traces (preserve agentic behavior)
    try:
        ds = load_dataset(SFT_DATASETS[1], split="train", streaming=True)
        for i, ex in enumerate(ds):
            if i >= args.n // 2:
                break
            q = ex.get("query") or ex.get("question") or ""
            ans = ex.get("answers") or ex.get("response") or ""
            if q and ans:
                rows.append({"messages": [
                    {"role": "user", "content": str(q)},
                    {"role": "assistant", "content": json.dumps(ans)
                     if not isinstance(ans, str) else ans}]})
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] {SFT_DATASETS[1]} failed: {e}")
    # reasoning/thinking traces — heal must REINFORCE thinking, not erase it,
    # or the model loses the planning/debugging that makes it good at agents.
    for d in ("open-thoughts/OpenThoughts-114k", "glaiveai/reasoning-v1-20m"):
        try:
            ds = load_dataset(d, split="train", streaming=True)
            for i, ex in enumerate(ds):
                if i >= args.n // 4:
                    break
                u = ex.get("question") or ex.get("problem") or ex.get("prompt") or ""
                a = ex.get("response") or ex.get("answer") or ex.get("text") or ""
                if u and a:
                    rows.append({"messages": [
                        {"role": "user", "content": str(u)},
                        {"role": "assistant", "content": str(a)}]})
            print(f"  + reasoning traces from {d}")
            break
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] reasoning {d} failed: {str(e)[:50]}")
    # ANTI-CATASTROPHIC-FORGETTING: research says mix ~30-50% general data during
    # recovery or the model collapses off-distribution. Add a general instruction
    # slice sized to ~35% of the heal set.
    target_general = int(len(rows) * 0.55)   # ~35% of final mix
    for d in ("HuggingFaceH4/ultrachat_200k", "allenai/tulu-3-sft-mixture"):
        try:
            ds = load_dataset(d, split="train", streaming=True)
            got = 0
            for ex in ds:
                if got >= target_general:
                    break
                msgs = ex.get("messages") or ex.get("conversations")
                if isinstance(msgs, list) and len(msgs) >= 2:
                    rows.append({"messages": msgs[:2]})
                    got += 1
            print(f"  + {got} general (anti-forgetting) from {d}")
            break
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] general {d} failed: {str(e)[:50]}")
    return rows


def load_mine_pairs():
    """Your own (prompt,completion) pairs from heal/mine/*.jsonl — best signal."""
    mine = os.path.join(ROOT, "heal", "mine")
    rows = []
    if not os.path.isdir(mine):
        return rows
    for fn in os.listdir(mine):
        if not fn.endswith(".jsonl"):
            continue
        for line in open(os.path.join(mine, fn), errors="ignore"):
            try:
                o = json.loads(line)
                if "messages" in o:
                    rows.append({"messages": o["messages"]})
                elif "prompt" in o and "completion" in o:
                    rows.append({"messages": [
                        {"role": "user", "content": o["prompt"]},
                        {"role": "assistant", "content": o["completion"]}]})
            except json.JSONDecodeError:
                continue
    return rows


def write_split(rows, out_dir=DATA_DIR, valid_frac=0.05):
    os.makedirs(out_dir, exist_ok=True)
    before = len(rows)
    rows = [r for r in rows if english_pair(r)]
    print(f"  english-only filter: kept {len(rows)}/{before} pairs")
    import random
    random.seed(42)
    random.shuffle(rows)
    n_valid = max(1, int(len(rows) * valid_frac))
    valid, train = rows[:n_valid], rows[n_valid:]
    for name, data in [("train", train), ("valid", valid)]:
        with open(os.path.join(out_dir, f"{name}.jsonl"), "w") as f:
            for r in data:
                f.write(json.dumps(r) + "\n")
    return len(train), len(valid)


def write_config(args):
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    # Research-backed schedule: cosine decay with warmup (forward-KL recovery
    # phase uses LR ~2e-5 -> 2e-6). mlx-lm builds this from the lr_schedule block.
    peak = args.learning_rate
    end = peak / 10
    warmup = max(5, args.iters // 20)        # 5% of steps (arXiv 2602.04998) — was hardcoded 100, which
    # exceeded total iters on small corpora → LR ramped into the run → loss-spike divergence. FIXED.
    yaml = f"""# Auto-generated QLoRA heal config (research-backed) for GLM-5.2
fine_tune_type: lora
num_layers: {args.num_layers}
lora_parameters:
  rank: {args.rank}
  scale: {args.scale}
  dropout: 0.1
lr_schedule:
  name: cosine_decay
  warmup: {warmup}
  warmup_init: 1e-7
  arguments: [{peak}, {args.iters}, {end}]
"""
    open(CONFIG, "w").write(yaml)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/GLM-5.2-demolished-mxmix")
    ap.add_argument("--mode", choices=["distill", "sft"], default="distill")
    ap.add_argument("--n", type=int, default=2000, help="sft sample budget")
    ap.add_argument("--per-lang", type=int, default=80, help="distill prompts/lang")
    # teacher (distill mode)
    ap.add_argument("--teacher-model", default="glm-5.2")
    ap.add_argument("--teacher-url", default="https://api.z.ai/v1")
    ap.add_argument("--sleep", type=float, default=0.3)
    # lora hyperparams
    ap.add_argument("--iters", type=int, default=1500)
    ap.add_argument("--num-layers", type=int, default=16,
                    help="adapter on last N layers; raise for deeper heal")
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--scale", type=float, default=20.0)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--max-seq-length", type=int, default=2048)
    ap.add_argument("--learning-rate", type=float, default=2e-5)  # research-backed
    ap.add_argument("--skip-data", action="store_true",
                    help="reuse existing heal/data, skip rebuild")
    ap.add_argument("--skip-train", action="store_true",
                    help="only build data, don't train")
    ap.add_argument("--no-mask-prompt", action="store_true",
                    help="train on the FULL sequence (no completion mask). Robust "
                         "against the mask.sum()==0 -> 0/0 NaN that mask-prompt hits "
                         "when a row has no completion tokens after truncation.")
    ap.add_argument("--data", default=DATA_DIR, help="training data dir (override, e.g. heal/data-v4)")
    ap.add_argument("--adapter-path", default=ADAPTER_DIR, help="LoRA output dir (override, e.g. heal/adapters-v4)")
    args = ap.parse_args()

    if not args.skip_data:
        print(f">> Building heal data (mode={args.mode})")
        rows = load_mine_pairs()
        if rows:
            print(f"  + {len(rows)} of YOUR pairs from heal/mine/ (best signal)")
        if args.mode == "distill":
            rows += build_distill(gather_prompts(args.per_lang), args)
        else:
            rows += build_sft(args)
        if not rows:
            sys.exit("  [stop] no training rows produced; check data sources")
        n_tr, n_va = write_split(rows)
        print(f"  wrote {n_tr} train / {n_va} valid -> {DATA_DIR}")

    write_config(args)
    if args.skip_train:
        print(">> --skip-train set; data + config ready. Done.")
        return

    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "--model", args.model,
        "--train",
        "--data", args.data,
        "--config", CONFIG,
        "--iters", str(args.iters),
        "--batch-size", str(args.batch_size),
        "--max-seq-length", str(args.max_seq_length),
        "--learning-rate", str(args.learning_rate),
        "--adapter-path", args.adapter_path,
        "--grad-checkpoint",             # fit big model in unified memory
    ]
    if not args.no_mask_prompt:
        cmd.append("--mask-prompt")      # train on assistant tokens only
    print(">> Training:", " ".join(cmd))
    # GLM_STREAM_EVAL=1 (serving default) does mx.eval(h) inside the layer loop — ILLEGAL inside training's
    # grad transform (ValueError: eval during compile/vmap). Force it off for the trainer subprocess.
    subprocess.run(cmd, check=True, env={**os.environ, "GLM_STREAM_EVAL": "0"})

    print(f"\n>> Adapters at {ADAPTER_DIR}")
    print(">> Serve with adapter:")
    print(f"   mlx_lm.server --model {args.model} --adapter-path {ADAPTER_DIR}")
    print(">> Then re-run eval to measure recovery:")
    print("   python scripts/07_eval.py --label healed")
    print(">> (Optional) fuse adapter into weights for a standalone model:")
    print(f"   mlx_lm.fuse --model {args.model} --adapter-path {ADAPTER_DIR} "
          f"--save-path models/GLM-5.2-demolished-healed")
    print("   NOTE: fusing a mixed-precision model can be lossy; serving with "
          "--adapter-path is the safe path.")


if __name__ == "__main__":
    main()
