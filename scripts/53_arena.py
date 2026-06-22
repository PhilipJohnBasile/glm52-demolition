#!/usr/bin/env python3
"""The Arena — PROVE the kill. Run the SAME verified coding tasks through OUR local
engine and the major models (GPT-5.6, Gemini-3, DeepSeek-V4, Qwen, Kimi, the FULL
GLM-5.2, …) and score EVERYONE with the SAME real verifier (compile + run + tests,
via src/verifiers). The leaderboard is the proof: a 99GB local specialist that
VERIFIES beats giants that GUESS — and it's free, private, and unlimited.

Contestants (any OpenAI-compatible model id, routed via OpenRouter by default):
  ours            — our local server, single-shot (raw capability of the demolished model)
  ours+loop       — our local server + the agentic loop (50): verify→repair→harden
  <provider/model>      — e.g. openai/gpt-5.6  (single-shot raw capability)
  <provider/model>+loop — same model, but given OUR agentic loop (the fair, metered fight)

Two honest columns: SINGLE-SHOT (their giant raw capability, where we expect to lose on
size) and +LOOP (verification in the loop — free for us, metered for them). Score on
HELD-OUT tests when a task provides them, so +loop measures real correctness, not
metric-gaming.

  export OPENROUTER_API_KEY=...           # for the cloud contestants
  python scripts/53_arena.py --tasks eval/tasks.jsonl --n 12 \
      --contestants ours,ours+loop,openai/gpt-5.6,google/gemini-3-pro,deepseek/deepseek-v4,zai/glm-5.2
  python scripts/53_arena.py --selftest   # GPU/API-free logic check
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from verifiers import verify  # noqa: E402

_spec = importlib.util.spec_from_file_location("agentic", os.path.join(HERE, "50_agentic_loop.py"))
agentic = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(agentic)

OPENROUTER = "https://openrouter.ai/api/v1"
LOCAL = os.environ.get("LOCAL_BASE_URL", "http://localhost:8080/v1")


def _extract(text):
    m = re.findall(r"```[a-zA-Z0-9]*\n(.*?)```", text, re.S)
    return (m[-1] if m else text).strip()


def chat(base_url, key, model, prompt, temp=0.0, max_tokens=1400):
    hdr = {"Content-Type": "application/json"}
    if key:
        hdr["Authorization"] = f"Bearer {key}"
    body = json.dumps({"model": model, "temperature": temp, "max_tokens": max_tokens,
                       "messages": [{"role": "system", "content":
                                     "Expert engineer. Output ONLY one fenced code block."},
                                    {"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(base_url + "/chat/completions", body, hdr)
    return json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]["content"]


def resolve(contestant):
    """Map a contestant spec to (generate_fn, uses_loop). generate_fn(task)->code."""
    loop = contestant.endswith("+loop")
    name = contestant[:-5] if loop else contestant
    if name == "ours":
        base, key, model = LOCAL, None, os.environ.get("MODEL_ID", "models/GLM-5.2-q3a4-v2")
    else:                                                    # cloud model via OpenRouter
        base = os.environ.get("OPENROUTER_BASE", OPENROUTER)
        key = os.environ.get("OPENROUTER_API_KEY")
        model = name

    def single(task):
        p = f"Task ({task.get('lang')}): {task['prompt']}\nWrite a correct solution. Code only."
        return _extract(chat(base, key, model, p))

    if not loop:
        return single, False

    def with_loop(task):                                     # OUR agentic loop, any model
        def propose(t, lang, diag, prev, temp):
            if diag:
                u = (f"Task ({lang}): {t}\n\nPrev:\n```{lang}\n{prev}\n```\nFAILED:\n{diag}\n"
                     "Fix the root cause. Full corrected code only.")
            else:
                u = f"Task ({lang}): {t}\nWrite a correct solution. Code only."
            return _extract(chat(base, key, model, u, temp))
        sol, _ = agentic.agentic_solve(propose, task.get("lang"), task["prompt"],
                                       task.get("harness", ""), budget=6, branch=2, log=lambda *a: None)
        return sol or ""
    return with_loop, True


def score_one(task, code):
    """Score on HELD-OUT tests if present (so +loop isn't circular), else the harness."""
    tests = task.get("hidden") or task.get("harness", "")
    if not code:
        return False
    r = verify(task.get("lang", ""), code, tests)
    return r.passed and r.stage != "skip"                # a no-toolchain SKIP must NOT count as solved (false-pass)


def run_arena(tasks, contestants, log=print):
    board = {}
    for c in contestants:
        gen, loop = resolve(c)
        npass = 0
        for t in tasks:
            try:
                code = gen(t)
                npass += int(score_one(t, code))
            except Exception as e:  # noqa: BLE001
                log(f"    {c} failed on a task: {str(e)[:60]}")
        board[c] = npass
        log(f"  {c:34} {npass}/{len(tasks)}  ({100*npass//max(len(tasks),1)}%)")
    return board


def selftest():
    """API-free: stub the model callers; a 'weak' contestant fails an edge case single-
    shot but its +loop variant repairs it -> proves the harness scores loop>single."""
    tasks = [{"lang": "python", "prompt": "add(a,b)=a+b",
              "harness": "assert add(2,3)==5", "hidden": "assert add(2,3)==5 and add(-1,1)==0"}]
    calls = {"n": 0}

    def fake_resolve(c):
        loop = c.endswith("+loop")
        def single(task):
            return "def add(a,b): return a-b"                # wrong
        def withloop(task):
            def propose(t, lang, diag, prev, temp):
                return "def add(a,b): return a+b" if diag else "def add(a,b): return a-b"
            sol, _ = agentic.agentic_solve(propose, "python", task["prompt"],
                                           task["harness"], budget=3, branch=1, log=lambda *a: None)
            return sol or ""
        return (withloop if loop else single), loop

    global resolve
    real, resolve = resolve, fake_resolve
    board = run_arena(tasks, ["weak", "weak+loop"], log=lambda *a: None)
    resolve = real
    ok = board["weak"] == 0 and board["weak+loop"] == 1
    print(f"  selftest: single-shot {board['weak']}/1, +loop {board['weak+loop']}/1 "
          f"(loop repairs to pass held-out tests)  {'PASS ✅' if ok else 'FAIL'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--tasks", default=os.path.join(HERE, "..", "eval", "tasks.jsonl"))
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--contestants", default="ours,ours+loop")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    if args.selftest:
        raise SystemExit(0 if selftest() else 1)
    tasks = [json.loads(l) for l in open(args.tasks) if l.strip()][:args.n]
    contestants = [c.strip() for c in args.contestants.split(",") if c.strip()]
    print(f"  Arena: {len(contestants)} contestants × {len(tasks)} tasks, scored by REAL "
          f"compile+run+test\n")
    board = run_arena(tasks, contestants)
    ranked = sorted(board.items(), key=lambda kv: -kv[1])
    print("\n  === LEADERBOARD (real-verifier pass-rate) ===")
    for i, (c, s) in enumerate(ranked, 1):
        print(f"  {i}. {c:34} {s}/{len(tasks)}")
    if args.out:
        json.dump(board, open(args.out, "w"), indent=2)


if __name__ == "__main__":
    main()
