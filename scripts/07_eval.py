#!/usr/bin/env python3
"""Per-language agentic eval + FLAGSHIP HEAD-TO-HEAD.

Scores tasks (executing code where a toolchain exists) against your local model,
and optionally against the real cloud GLM-5.2 flagship on the SAME tasks, so
"did we top it on these languages?" becomes an actual A/B number.

  # serve the model under test (terminal 1)
  MODEL=models/GLM-5.2-demolished-mxmix bash scripts/05_serve.sh  # +--adapter-path heal/adapters
  # head-to-head vs flagship (terminal 2)
  ZAI_API_KEY=... python scripts/07_eval.py --label healed --vs-flagship

Without --vs-flagship it just reports your model's per-language pass rate.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from exec_check import check  # noqa: E402

TASKS = os.path.join(HERE, "..", "eval", "tasks.jsonl")


def chat(base_url, model, prompt, api_key=None, think=None):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0, "max_tokens": 2048,
    }
    if think is not None:  # toggle reasoning via the chat template
        payload["chat_template_kwargs"] = {"enable_thinking": bool(think)}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(f"{base_url}/chat/completions", body, headers)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"], time.time() - t0


def anthropic_chat(model, prompt, api_key):
    """Call Anthropic (Fable) so we can head-to-head against the frontier model."""
    body = json.dumps({"model": model, "max_tokens": 2048,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", body,
        {"content-type": "application/json", "x-api-key": api_key,
         "anthropic-version": "2023-06-01"})
    t0 = time.time()
    data = json.loads(urllib.request.urlopen(req, timeout=600).read())
    text = "".join(b.get("text", "") for b in data.get("content", []))
    return text, time.time() - t0


def score_all(tasks, base_url, model, api_key=None, think=None, chat_fn=None):
    """Return {lang: [pass, runnable, skipped, total_latency]} and marks."""
    by_lang = defaultdict(lambda: [0, 0, 0, 0.0])
    marks = {}
    for t in tasks:
        try:
            if chat_fn:                                  # e.g. Fable via Anthropic
                reply, dt = chat_fn(model, t["prompt"], api_key)
            else:
                reply, dt = chat(base_url, model, t["prompt"], api_key, think)
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] {model} call failed on {t['id']}: {str(e)[:50]}")
            reply, dt = "", 0.0
        ok = check(t, reply)
        marks[t["id"]] = ok
        b = by_lang[t["lang"]]
        b[3] += dt
        if ok is None:
            b[2] += 1
        else:
            b[1] += 1
            b[0] += int(bool(ok))
    return by_lang, marks


def report(label, by_lang, scarce):
    print(f"\n=== {label}: per-language pass rate + avg latency ===")
    for lang in sorted(by_lang):
        p, tot, sk, lat = by_lang[lang]
        n = (tot + sk) or 1
        rate = f"{p}/{tot}" if tot else "n/a"
        watch = "  <-- watch" if lang in scarce else ""
        print(f"  {lang:11} {rate:>6}   {lat / n:5.1f}s/task{watch}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2",
                    help="mlx_lm.server wants the model PATH, not 'local'")
    ap.add_argument("--label", default="run")
    ap.add_argument("--think", choices=["on", "off", "both", "default"],
                    default="default", help="reasoning mode for the local model")
    ap.add_argument("--vs-flagship", action="store_true",
                    help="also run the real GLM-5.2 flagship on the same tasks")
    ap.add_argument("--flagship-model", default="glm-5.2")
    ap.add_argument("--flagship-url", default="https://api.z.ai/v1")
    ap.add_argument("--vs-fable", action="store_true",
                    help="head-to-head vs Anthropic Fable (needs ANTHROPIC_API_KEY)")
    ap.add_argument("--fable-model", default="claude-fable-5")
    args = ap.parse_args()
    scarce = {"rust"}
    tasks = [json.loads(l) for l in open(TASKS)]

    modes = {"on": [True], "off": [False], "both": [True, False],
             "default": [None]}[args.think]
    runs = {}
    for think in modes:
        name = {True: "think-ON", False: "think-OFF", None: "default"}[think]
        print(f">> Scoring LOCAL ({name})...")
        by_lang, _ = score_all(tasks, args.base_url, args.model, think=think)
        runs[name] = by_lang
        report(f"{args.label} [{name}]", by_lang, scarce)

    if args.think == "both":
        on, off = runs["think-ON"], runs["think-OFF"]
        print("\n=== thinking trade-off (ON vs OFF) ===")
        for lang in sorted(on):
            op, ot, _, ol = on[lang]
            fp, ft, _, fl = off[lang]
            don = (ol / ((ot) or 1))
            doff = (fl / ((ft) or 1))
            print(f"  {lang:11} quality {op}/{ot} vs {fp}/{ft}   "
                  f"latency {don:.1f}s vs {doff:.1f}s  "
                  f"(think-on costs {don - doff:+.1f}s)")
        print("  -> use think-ON where it raises pass-rate; OFF where it only "
              "adds latency. The proxy (08) automates this per step.")

    flag = None
    if args.vs_flagship:
        key = os.environ.get("ZAI_API_KEY")
        if not key:
            sys.exit("  [stop] --vs-flagship needs ZAI_API_KEY")
        print(">> Scoring FLAGSHIP GLM-5.2 on the same tasks...")
        flag, _ = score_all(tasks, args.flagship_url, args.flagship_model,
                            api_key=key)
        # compare flagship to the local model's BEST mode per language.
        best = runs.get("think-ON") or next(iter(runs.values()))
        print(f"\n=== {args.label}: LOCAL (best mode) vs FLAGSHIP ===")
        topped = tied = behind = 0
        for lang in sorted(best):
            p, tot = best[lang][0], best[lang][1]
            fp, ftot = flag[lang][0], flag[lang][1]
            if tot and ftot:
                if p > fp:
                    v, topped = "TOPPED ✅", topped + 1
                elif p == fp:
                    v, tied = "tied", tied + 1
                else:
                    v, behind = "behind", behind + 1
            else:
                v = "n/a"
            print(f"  {lang:11} local {p}/{tot}   flagship {fp}/{ftot}   -> {v}")
        print(f"\n  HEAD-TO-HEAD: topped {topped}, tied {tied}, behind {behind}")
        print("  'Topped' on your stack is the real goal — not the public arena.")

    fable = None
    if args.vs_fable:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            sys.exit("  [stop] --vs-fable needs ANTHROPIC_API_KEY")
        print(f">> Scoring FABLE ({args.fable_model}) on the same tasks...")
        fable, _ = score_all(tasks, None, args.fable_model, api_key=key,
                             chat_fn=anthropic_chat)
        best = runs.get("think-ON") or next(iter(runs.values()))
        print(f"\n=== {args.label}: LOCAL (your niche) vs FABLE ===")
        t = ti = b = 0
        for lang in sorted(best):
            p, tot = best[lang][0], best[lang][1]
            fp, ftot = fable[lang][0], fable[lang][1]
            if tot and ftot:
                if p > fp: v, t = "BEAT FABLE ✅", t + 1
                elif p == fp: v, ti = "tied", ti + 1
                else: v, b = "behind", b + 1
            else:
                v = "n/a"
            print(f"  {lang:11} local {p}/{tot}   fable {fp}/{ftot}   -> {v}")
        print(f"\n  vs FABLE: beat {t}, tied {ti}, behind {b} "
              f"(of {t+ti+b} comparable). With best-of-N verification (26), "
              "re-run candidates that lose to recover more.")

    out = os.path.join(HERE, "..", "eval", f"result-{args.label}.json")
    json.dump({"label": args.label,
               "runs": {k: {lg: v for lg, v in d.items()} for k, d in runs.items()},
               "flagship": ({k: v for k, v in flag.items()} if flag else None)},
              open(out, "w"), indent=2)
    print(f"\n  saved -> {out}")


if __name__ == "__main__":
    main()
