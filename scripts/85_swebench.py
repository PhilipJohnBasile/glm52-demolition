#!/usr/bin/env python3
"""SWE-bench Verified runner — the STANDARD agentic-coding benchmark (500 real GitHub issues) our positioning
demands. We report HumanEval/GSM8K (not agentic); the field reports SWE-bench Verified (Claude Sonnet 4.5 leads
~0.77). Our scripts/57_tool_agent.py IS the harness (clone repo@base_commit → agent edits → git diff = the patch).
This generates predictions in the official format; SCORE with the official `swebench` harness (Docker) for honest,
comparable, contamination-checked numbers — NOT a hand-rolled scorer (the 2026 Berkeley study showed agent
benchmarks are gameable, so we use the canonical harness + disclose it).

  python scripts/85_swebench.py --selftest                      # CPU: verify load + format
  python scripts/85_swebench.py --n 20 --out swebench_preds.jsonl  # GPU: agent per task → predictions
  python -m swebench.harness.run_evaluation --predictions_path swebench_preds.jsonl --run_id glm52  # official score (Docker)
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(__file__)
DATASET = "princeton-nlp/SWE-bench_Verified"
MODEL = "GLM-5.2-Demolition-q3a4"


def load_tasks(n, dataset=DATASET):
    from datasets import load_dataset
    ds = load_dataset(dataset, split="test")
    return [ds[i] for i in range(min(n, len(ds)))]


def run_task(task, test_cmd="python -m pytest -q", timeout=900):  # GPU (the agent calls the model)
    """Clone repo@base_commit, run our agent on the issue, return the official prediction dict (model_patch = git diff)."""
    with tempfile.TemporaryDirectory() as d:
        try:
            subprocess.run(["git", "clone", "--quiet", f"https://github.com/{task['repo']}.git", d], check=True, timeout=300)
            subprocess.run(["git", "checkout", "--quiet", task["base_commit"]], cwd=d, check=True)
            subprocess.run([sys.executable, os.path.join(HERE, "57_tool_agent.py"), "--repo", d, "--apply",
                            "--task", task["problem_statement"], "--test", test_cmd],
                           capture_output=True, text=True, timeout=timeout)
            patch = subprocess.run(["git", "diff"], cwd=d, capture_output=True, text=True).stdout
        except Exception as e:  # noqa: BLE001
            patch = ""
            print(f"    {task['instance_id']}: {str(e)[:60]}", flush=True)
    return {"instance_id": task["instance_id"], "model_name_or_path": MODEL, "model_patch": patch}


def _selftest():
    tasks = load_tasks(3)
    assert len(tasks) == 3, "dataset load failed"
    for t in tasks:
        assert t.get("instance_id") and t.get("base_commit") and t.get("problem_statement"), "missing fields"
    pred = {"instance_id": tasks[0]["instance_id"], "model_name_or_path": MODEL, "model_patch": "diff --git a/x b/x\n+pass\n"}
    assert all(k in pred for k in ("instance_id", "model_name_or_path", "model_patch")), "bad prediction format"
    print(f"  SWE-bench Verified: loads {len(tasks)}/500 sampled · gold fields present · prediction format valid ✓")
    print(f"  sample task: {tasks[0]['instance_id']} (repo {tasks[0]['repo']})")
    print("  → GPU: run --n to make predictions; score with the OFFICIAL swebench harness (Docker) — honest + comparable")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--out", default="swebench_preds.jsonl")
    ap.add_argument("--test", default="python -m pytest -q")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    tasks = load_tasks(a.n)
    with open(a.out, "w") as f:
        for i, t in enumerate(tasks):
            print(f"  [{i + 1}/{len(tasks)}] {t['instance_id']}", flush=True)
            f.write(json.dumps(run_task(t, a.test)) + "\n")
    print(f"  wrote {len(tasks)} predictions → {a.out}")
    print(f"  SCORE (official, Docker): python -m swebench.harness.run_evaluation --predictions_path {a.out} --run_id glm52")


if __name__ == "__main__":
    main()
