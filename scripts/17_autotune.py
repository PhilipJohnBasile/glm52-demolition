#!/usr/bin/env python3
"""Auto-tune the smart+fast operating point. Sweeps serve-time speed knobs on a
fixed model and measures BOTH axes — eval pass-rate (smart) and tokens/sec
(fast) — then reports the Pareto frontier and a recommendation.

Cheap knobs (no re-quantize): speculative num_draft (0=off,3,5,8), thinking mode.
For each config it serves the model, benchmarks tokens/sec on coding prompts,
runs the eval suite, then tears down.

  python scripts/17_autotune.py --model models/GLM-5.2-demolished-mxmix \
      --adapter heal/adapters --draft <tokenizer-compatible-draft>

Without --draft it sweeps thinking modes only (speculative needs a draft).
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(__file__)
BENCH_PROMPTS = [
    "Write a Python function to merge two sorted lists.",
    "Refactor this to use async/await: function f(cb){setTimeout(cb,1)}",
    "Explain and fix: a Rust borrow-checker error on a mutable reference.",
]


def wait_ready(url, timeout=180):
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url + "/models", timeout=2)
            return True
        except Exception:  # noqa: BLE001
            time.sleep(1)
    return False


def bench_tps(url, think):
    """tokens/sec over benchmark prompts (lower-is-slower)."""
    total_tok = total_t = 0.0
    for p in BENCH_PROMPTS:
        body = {"model": "local", "messages": [{"role": "user", "content": p}],
                "temperature": 0.0, "max_tokens": 256,
                "chat_template_kwargs": {"enable_thinking": think}}
        req = urllib.request.Request(url + "/chat/completions",
                                     json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        t0 = time.time()
        data = json.loads(urllib.request.urlopen(req, timeout=300).read())
        dt = time.time() - t0
        tok = data.get("usage", {}).get("completion_tokens", 0)
        total_tok += tok
        total_t += dt
    return total_tok / total_t if total_t else 0.0


def eval_passrate(label, think):
    """Run the eval suite against localhost:8080, return overall pass fraction."""
    mode = "on" if think else "off"
    out = subprocess.run(
        [sys.executable, os.path.join(HERE, "07_eval.py"),
         "--label", label, "--think", mode],
        capture_output=True, text=True)
    # parse the saved result json
    rf = os.path.join(HERE, "..", "eval", f"result-{label}.json")
    try:
        d = json.load(open(rf))
        run = next(iter(d["runs"].values()))
        p = sum(v[0] for v in run.values())
        tot = sum(v[1] for v in run.values())
        return p / tot if tot else 0.0
    except Exception:  # noqa: BLE001
        return 0.0


def serve(model, adapter, draft, num_draft, port=8080):
    args = [sys.executable, "-m", "mlx_lm", "server", "--model", model,
            "--port", str(port), "--prompt-cache-size", "8"]
    if adapter and os.path.isdir(adapter):
        args += ["--adapter-path", adapter]
    if draft and num_draft > 0:
        args += ["--draft-model", draft, "--num-draft-tokens", str(num_draft)]
    return subprocess.Popen(args, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter", default="heal/adapters")
    ap.add_argument("--draft", default=None, help="tokenizer-compatible draft")
    ap.add_argument("--url", default="http://localhost:8080/v1")
    args = ap.parse_args()

    # configs: (num_draft, think). num_draft=0 -> speculative off.
    drafts = [0, 3, 5, 8] if args.draft else [0]
    configs = [(nd, th) for nd in drafts for th in (True, False)]

    results = []
    for nd, think in configs:
        name = f"draft{nd}-think{'On' if think else 'Off'}"
        print(f">> config {name}: serving...")
        proc = serve(args.model, args.adapter, args.draft, nd)
        try:
            if not wait_ready(args.url):
                print("   server didn't come up, skipping"); continue
            tps = bench_tps(args.url, think)
            acc = eval_passrate(f"tune-{name}", think)
            results.append({"config": name, "num_draft": nd, "think": think,
                            "tok_per_s": round(tps, 1), "pass_rate": round(acc, 3)})
            print(f"   {name}: {tps:.1f} tok/s  pass={acc:.1%}")
        finally:
            proc.terminate()
            proc.wait()
            time.sleep(2)

    # Pareto frontier: not dominated on both speed AND accuracy.
    def dominated(r):
        return any(o["tok_per_s"] >= r["tok_per_s"] and o["pass_rate"] >= r["pass_rate"]
                   and o != r and (o["tok_per_s"] > r["tok_per_s"] or
                                   o["pass_rate"] > r["pass_rate"]) for o in results)
    pareto = [r for r in results if not dominated(r)]

    print("\n=== all configs (smart vs fast) ===")
    for r in sorted(results, key=lambda x: -x["pass_rate"]):
        star = " *PARETO" if r in pareto else ""
        print(f"  {r['config']:20} {r['tok_per_s']:6.1f} tok/s  "
              f"pass {r['pass_rate']:.1%}{star}")
    if pareto:
        # recommend: highest pass-rate among configs within 10% of best speed,
        # else the best pass-rate on the frontier.
        best_speed = max(r["tok_per_s"] for r in pareto)
        fast_enough = [r for r in pareto if r["tok_per_s"] >= 0.9 * best_speed]
        rec = max(fast_enough or pareto, key=lambda r: r["pass_rate"])
        print(f"\n  RECOMMEND: {rec['config']}  "
              f"({rec['tok_per_s']} tok/s, {rec['pass_rate']:.1%} pass)")
        print(f"  -> serve: DRAFT_MODEL={args.draft or ''} "
              f"NUM_DRAFT={rec['num_draft']} MODEL={args.model} bash scripts/05_serve.sh")
    json.dump(results, open(os.path.join(HERE, "..", "eval", "autotune.json"), "w"),
              indent=2)


if __name__ == "__main__":
    main()
