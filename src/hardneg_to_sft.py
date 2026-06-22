"""Close the flywheel loop (#16) — turn mined hard-negatives into REPAIR-SFT data the next heal can use.
Each hard-neg is (good, bad) where bad = good + an injected bug that breaks its asserts. We format it as a
debugging example: the model sees the buggy code + the failing symptom and must produce the corrected code.
This is what makes the flywheel COMPOUND — without it the negs just pile up in a file.

  python src/hardneg_to_sft.py --in heal/hardnegs_rich.jsonl --out heal/_q_repair/train.jsonl
"""
import argparse
import json
import os

SYS = "You are an expert debugger. Given code that fails its tests, return the corrected code only."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="heal/hardnegs_rich.jsonl")
    ap.add_argument("--out", default="heal/_q_repair/train.jsonl")
    ap.add_argument("--max", type=int, default=5000)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    seen = set()
    n = 0
    with open(a.out, "w") as w:
        for line in open(a.inp):
            try:
                d = json.loads(line)
            except Exception:
                continue
            good, bad = d.get("good"), d.get("bad")
            if not good or not bad or bad == good or bad in seen:
                continue
            seen.add(bad)
            user = (f"This code fails its tests (verify stage: {d.get('stage', 'run')}). "
                    f"Fix it:\n\n```python\n{bad}\n```")
            asst = f"```python\n{good}\n```"
            w.write(json.dumps({"messages": [
                {"role": "system", "content": SYS},
                {"role": "user", "content": user},
                {"role": "assistant", "content": asst}]}) + "\n")
            n += 1
            if n >= a.max:
                break
    print(f"  wrote {n} repair-SFT examples -> {a.out}  (heal: --data heal/_q_repair when the GPU frees)")


if __name__ == "__main__":
    main()
