#!/usr/bin/env python3
"""③ The compounding flywheel. Every agentic/team run (50/51, via --trace-out) leaves
a trace; this harvests them into training data for the NEXT GRPO/heal/KD pass, so the
model gets better at exactly the tasks it STRUGGLED with — on YOUR distribution. Run
nightly on the day's traces and it compounds while you sleep; a static cloud model
can't. Outputs:
  heal/mine/flywheel_sft.jsonl  — (prompt -> the final correct solution) for tasks that
                                  needed repair, so next time it's first-try (SFT/KD).
  heal/flywheel_targets.jsonl   — still-unsolved tasks -> hard targets for the next GRPO.

  python scripts/50_agentic_loop.py ... --trace-out logs/agentic_traces.jsonl   # collect
  python scripts/52_flywheel.py --traces logs/agentic_traces.jsonl              # harvest
"""
import argparse
import glob
import json
import os


def harvest(trace_files, sft_out, grpo_out, min_iters):
    sft, hard, seen = [], [], set()
    for tf in trace_files:
        if not os.path.exists(tf):
            continue
        for line in open(tf):
            if not line.strip():
                continue
            tr = json.loads(line)
            key = (tr.get("lang", ""), tr.get("task", ""))
            if key in seen:
                continue
            seen.add(key)
            struggled = tr.get("iters", 0) >= min_iters or tr.get("adversarial_rounds", 0) >= 1
            if tr.get("solved") and tr.get("solution") and struggled:
                sft.append({"messages": [
                    {"role": "user", "content": f"({tr.get('lang')}) {tr.get('task')}"},
                    {"role": "assistant",
                     "content": f"```{tr.get('lang')}\n{tr['solution']}\n```"}]})
            elif not tr.get("solved"):
                last = (tr.get("attempts") or [{}])[-1]
                hard.append({"prompt": tr.get("task"), "lang": tr.get("lang"),
                             "harness": tr.get("harness", ""), "last_diag": last.get("diag", "")})
    os.makedirs(os.path.dirname(sft_out) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(grpo_out) or ".", exist_ok=True)
    with open(sft_out, "w") as f:
        f.writelines(json.dumps(e) + "\n" for e in sft)
    with open(grpo_out, "w") as f:
        f.writelines(json.dumps(e) + "\n" for e in hard)
    return len(sft), len(hard)


def selftest():
    import tempfile
    d = tempfile.mkdtemp()
    tf = os.path.join(d, "tr.jsonl")
    with open(tf, "w") as f:
        f.write(json.dumps({"lang": "python", "task": "add", "solved": True, "iters": 3,
                            "solution": "def add(a,b): return a+b", "attempts": []}) + "\n")
        f.write(json.dumps({"lang": "python", "task": "easy", "solved": True, "iters": 1,
                            "solution": "x=1", "attempts": []}) + "\n")           # first-try -> skip
        f.write(json.dumps({"lang": "rust", "task": "hard", "solved": False, "iters": 8,
                            "harness": "h", "attempts": [{"diag": "E0382 borrow"}]}) + "\n")
    s, h = harvest([tf], os.path.join(d, "sft.jsonl"), os.path.join(d, "grpo.jsonl"), 2)
    ok = s == 1 and h == 1          # struggled-solved kept, first-try skipped, unsolved -> hard
    print(f"  selftest: {s} SFT target (struggled+solved), {h} hard target (unsolved), "
          f"first-try skipped  {'PASS ✅' if ok else 'FAIL'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces", nargs="+", default=["logs/agentic_traces.jsonl"])
    ap.add_argument("--sft-out", default="heal/mine/flywheel_sft.jsonl")
    ap.add_argument("--grpo-out", default="heal/flywheel_targets.jsonl")
    ap.add_argument("--min-iters", type=int, default=2)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        raise SystemExit(0 if selftest() else 1)
    files = []
    for t in args.traces:
        files += glob.glob(t)
    n_sft, n_hard = harvest(files, args.sft_out, args.grpo_out, args.min_iters)
    print(f"  harvested {n_sft} SFT/KD targets (struggled-but-solved) -> {args.sft_out}")
    print(f"  {n_hard} still-unsolved hard targets -> {args.grpo_out} (next GRPO focus)")
    print("  -> re-heal/GRPO to bank it; the model compounds on YOUR distribution.")


if __name__ == "__main__":
    main()
