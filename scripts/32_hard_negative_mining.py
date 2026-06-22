#!/usr/bin/env python3
"""Hard-negative mining flywheel — turn every task we LOSE to Fable into training
data, so the next heal closes exactly the gap. A self-improving loop targeting
Fable directly on our niche (something Fable's team can't run on YOUR stack).

For each eval task: get our model's answer and Fable's; check both with the real
verifier (exec_check). Harvest a training pair for the tasks we lose, with the
BEST available correct target:
  1) our own toolchain-verified repair (purest: self-generated + verified), else
  2) Fable's answer if it passes the check (distill the win on our weak spots).

  # serve the model (+08 proxy), set ANTHROPIC_API_KEY, then:
  python scripts/32_hard_negative_mining.py --base-url http://localhost:8081/v1

Output -> heal/mine/hard_negatives.jsonl  (feed the next heal; weight it up).
"""
import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from exec_check import check, extract_code  # noqa: E402

TASKS = os.path.join(HERE, "..", "eval", "tasks.jsonl")
OUT = os.path.join(HERE, "..", "heal", "mine", "hard_negatives.jsonl")


def local_chat(base_url, prompt, temperature=0.0):
    body = json.dumps({"model": "local", "temperature": temperature, "max_tokens": 2048,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(base_url + "/chat/completions", body,
                                 {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=400).read())[
        "choices"][0]["message"]["content"]


def fable_chat(prompt, key, model):
    body = json.dumps({"model": model, "max_tokens": 2048,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", body,
        {"content-type": "application/json", "x-api-key": key,
         "anthropic-version": "2023-06-01"})
    data = json.loads(urllib.request.urlopen(req, timeout=400).read())
    return "".join(b.get("text", "") for b in data.get("content", []))


def try_verify_repair(task, base_url):
    """Best target: our own model, repaired against the toolchain until it passes.
    Returns a passing reply or None. Imports 30's loop in-process."""
    import importlib.util as u
    spec = u.spec_from_file_location("vr", os.path.join(HERE, "30_verify_repair.py"))
    vr = u.module_from_spec(spec)
    spec.loader.exec_module(vr)
    lang = task.get("lang", "")
    verify = vr.VERIFIERS.get(lang)
    if not verify:
        return None
    msgs = [{"role": "system", "content": "Return ONLY a fenced code block."},
            {"role": "user", "content": task["prompt"]}]
    for r in range(3):
        reply = vr.chat(base_url, msgs, temperature=0.0 if r == 0 else 0.5)
        code = extract_code(reply) or reply
        ok, diag = verify(code, task.get("harness", ""))
        if ok:
            return f"```{lang}\n{code}\n```"
        if ok is None:
            return None
        msgs += [{"role": "assistant", "content": f"```{lang}\n{code}\n```"},
                 {"role": "user", "content": f"The toolchain rejected that:\n{diag}\n"
                  "Fix all errors, return only the corrected code."}]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8081/v1")
    ap.add_argument("--fable-model", default="claude-fable-5")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    key = os.environ.get("ANTHROPIC_API_KEY")
    tasks = [json.loads(l) for l in open(TASKS)]
    harvested = []
    for t in tasks:
        try:
            local = local_chat(args.base_url, t["prompt"])
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] local failed {t['id']}: {str(e)[:40]}"); continue
        if check(t, local) is True:
            continue                                   # we already win; nothing to learn
        # we lost/failed -> find the best correct target
        target = try_verify_repair(t, args.base_url)   # 1) self, verified
        source = "self-verified"
        if not target and key:                         # 2) distill Fable's win
            try:
                fab = fable_chat(t["prompt"], key, args.fable_model)
                if check(t, fab) is True:
                    target, source = fab, "fable-distill"
            except Exception as e:  # noqa: BLE001
                print(f"  [warn] fable failed {t['id']}: {str(e)[:40]}")
        if target:
            harvested.append({"messages": [
                {"role": "user", "content": t["prompt"]},
                {"role": "assistant", "content": target}], "_src": source, "_id": t["id"]})
            print(f"  harvested {t['id']} ({t.get('lang')}) <- {source}")
    with open(args.out, "w") as f:
        f.write("\n".join(json.dumps({"messages": h["messages"]}) for h in harvested))
    by = {}
    for h in harvested:
        by[h["_src"]] = by.get(h["_src"], 0) + 1
    print(f"\n  {len(harvested)} hard-negatives -> {args.out}  {by}")
    print("  add to the next heal (weight x2-3): these are exactly where we trailed Fable.")


if __name__ == "__main__":
    main()
