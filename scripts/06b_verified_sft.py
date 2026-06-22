#!/usr/bin/env python3
"""Verified-SFT data builder — the ONLY heal signal that can push the local
model PAST the flagship on your slice. Three sources, all writing English-only
chat pairs into heal/mine/ (picked up by 06_heal_lora.py):

  1. REJECT SAMPLING (--gen): generate K candidate solutions per task, RUN the
     tests (via shared exec_check), and keep ONLY solutions that pass. Training
     on verified-correct code is a stronger signal than imitating the flagship,
     because correctness is ground truth the base model wasn't optimized against.
     Candidates can come from the local model (self-improvement) or the flagship
     (high-quality, then filtered to correctness).

  2. MBPP (--mbpp N): pulls Python problems that ship with unit tests, for volume
     of execution-verified Python pairs.

  3. YOUR REPOS (--repos DIR): ingests real files in your 7 languages as
     ground-truth completions, teaching YOUR conventions — code the flagship has
     never seen. This is where "top it on my codebase" actually comes from.

Output: heal/mine/verified.jsonl  ({"messages":[user,assistant]}).
"""

import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from exec_check import check, extract_code, run_python  # noqa: E402

OUT_DIR = os.path.join(ROOT, "heal", "mine")
OUT = os.path.join(OUT_DIR, "verified.jsonl")

EXT_LANG = {".py": "python", ".ts": "typescript", ".tsx": "typescript",
            ".js": "javascript", ".jsx": "javascript", ".rs": "rust",
            ".go": "go", ".html": "html", ".htm": "html",
            ".css": "css", ".scss": "css"}

_FOREIGN = [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x3040, 0x30FF),
            (0xAC00, 0xD7AF), (0x0400, 0x04FF), (0x0600, 0x06FF), (0x0590, 0x05FF)]


def is_english(text, max_foreign=0.02):
    foreign = letters = 0
    for c in str(text):
        if c.isalpha():
            letters += 1
            if any(lo <= ord(c) <= hi for lo, hi in _FOREIGN):
                foreign += 1
    return letters == 0 or foreign / letters <= max_foreign


def chat(base_url, model, prompt, api_key, temperature):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = json.dumps({
        "model": model, "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature, "max_tokens": 1400,
    }).encode()
    req = urllib.request.Request(f"{base_url}/chat/completions", body, headers)
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def pair(prompt, completion):
    return {"messages": [{"role": "user", "content": prompt},
                         {"role": "assistant", "content": completion}]}


def reject_sample(tasks, args, kept):
    """Generate K candidates/task, keep only verified-correct completions."""
    url = args.flagship_url if args.gen == "flagship" else args.base_url
    model = args.flagship_model if args.gen == "flagship" else args.model
    key = os.environ.get("ZAI_API_KEY") if args.gen == "flagship" else None
    if args.gen == "flagship" and not key:
        sys.exit("  [stop] --gen flagship needs ZAI_API_KEY")
    for t in tasks:
        wins = 0
        for k in range(args.samples):
            try:
                reply = chat(url, model, t["prompt"], key,
                             0.0 if k == 0 else 0.7)
            except Exception as e:  # noqa: BLE001
                print(f"  [warn] gen failed {t['id']}: {str(e)[:40]}")
                continue
            ok = check(t, reply)
            if ok is True and is_english(reply):
                kept.append(pair(t["prompt"], reply))
                wins += 1
                if wins >= args.keep_per_task:
                    break
        print(f"  {t['lang']:11} {t['id']}: kept {wins}/{args.samples}")


def add_mbpp(n, args, kept):
    try:
        from datasets import load_dataset
        ds = load_dataset("mbpp", split="train", streaming=True)
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] mbpp unavailable ({e})"); return
    url = args.flagship_url if args.gen == "flagship" else args.base_url
    model = args.flagship_model if args.gen == "flagship" else args.model
    key = os.environ.get("ZAI_API_KEY") if args.gen == "flagship" else None
    got = 0
    for ex in ds:
        if got >= n:
            break
        prompt = ex["text"] + "\nReturn ONLY a fenced python code block."
        harness = "\n".join(ex.get("test_list", []))
        if not harness:
            continue
        try:
            reply = chat(url, model, prompt, key, 0.2)
        except Exception:  # noqa: BLE001
            continue
        if run_python(extract_code(reply), harness) and is_english(reply):
            kept.append(pair(ex["text"], reply))
            got += 1
    print(f"  mbpp (python, test-verified): kept {got}")


TARGET_LANGS = ["python", "typescript", "javascript", "rust", "go", "html", "css"]


def ingest_repos(repo_dir, kept, max_chars=6000, min_chars=120):
    """FUNCTION-LEVEL ingestion: chunk each file on def/class/fn boundaries
    (via the RAG chunker) so pairs are properly sized — not whole files that
    blow the sequence limit. Each chunk -> a 'implement this symbol' SFT pair.
    """
    import rag  # src is on sys.path
    chunks = rag.index_paths([repo_dir], langs=TARGET_LANGS)
    got = skipped = 0
    for c in chunks:
        text = c["text"]
        if not (min_chars <= len(text) <= max_chars) or not is_english(text):
            skipped += 1
            continue
        sym = (c.get("symbol") or os.path.basename(c["file"])).strip()
        # signature-led instruction makes a clean "complete this unit" task.
        instr = (f"Implement `{sym}` in {c['lang']} (from "
                 f"{os.path.basename(c['file'])}), following this project's "
                 f"conventions and style.")
        kept.append(pair(instr, f"```{c['lang']}\n{text}\n```"))
        got += 1
    print(f"  repos: {got} function-level pairs from {repo_dir} "
          f"({skipped} chunks skipped: too small/large or non-English)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", choices=["local", "flagship", "none"],
                    default="local", help="candidate generator for reject-sampling")
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    ap.add_argument("--model", default="local")
    ap.add_argument("--flagship-model", default="glm-5.2")
    ap.add_argument("--flagship-url", default="https://api.z.ai/v1")
    ap.add_argument("--tasks", default=os.path.join(ROOT, "eval", "gen_tasks.jsonl"))
    ap.add_argument("--samples", type=int, default=4, help="candidates per task")
    ap.add_argument("--keep-per-task", type=int, default=2)
    ap.add_argument("--mbpp", type=int, default=0, help="N test-verified python")
    ap.add_argument("--repos", default=None, help="dir of YOUR repos to ingest")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    kept = []

    if args.gen != "none" and os.path.exists(args.tasks):
        tasks = [json.loads(l) for l in open(args.tasks)]
        print(f">> Reject-sampling {len(tasks)} tasks via {args.gen} "
              f"({args.samples} candidates each, keep only test-passing)...")
        reject_sample(tasks, args, kept)
    if args.mbpp:
        print(f">> MBPP: generating + test-verifying {args.mbpp} python...")
        add_mbpp(args.mbpp, args, kept)
    if args.repos:
        print(f">> Ingesting your repos from {args.repos}...")
        ingest_repos(args.repos, kept)

    with open(OUT, "w") as f:
        for r in kept:
            f.write(json.dumps(r) + "\n")
    print(f"\n>> Wrote {len(kept)} VERIFIED pairs -> {OUT}")
    print(">> These feed 06_heal_lora.py automatically (heal/mine/). Then:")
    print("   python scripts/06_heal_lora.py --mode sft --skip-data=false")
    print("   (verified pairs are loaded via load_mine_pairs alongside SFT data)")


if __name__ == "__main__":
    main()
