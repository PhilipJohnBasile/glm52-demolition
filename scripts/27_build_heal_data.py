#!/usr/bin/env python3
"""Build the BALANCED heal/data split (plan step 4). Your data + design heavy,
public function-completions capped, plus agentic + reasoning + anti-forgetting —
so the heal makes a real agent, not a style-mimic.

  python scripts/27_build_heal_data.py
"""
import glob
import json
import os
import random

random.seed(0)
ROOT = os.path.join(os.path.dirname(__file__), "..")


def load(name):
    p = os.path.join(ROOT, "heal", "mine", name)
    if not os.path.exists(p):
        return []
    out = []
    for l in open(p):                                  # parse ONCE + tolerate a corrupt line (was double-parse + crash-on-bad-line)
        if not l.strip():
            continue
        try:
            obj = json.loads(l)
        except ValueError:
            continue
        if "messages" in obj:
            out.append(obj)
    return out


rows = []
# --- YOUR data + niche (heavy) ---
rows += load("callsieve.jsonl")                    # your Rust, all
rows += load("aescode.jsonl")                      # design aesthetics, all 6k
rows += load("design_curriculum.jsonl") * 2        # canon/OKLCH/critique
rows += load("design_history.jsonl") * 2
rows += load("design_patterns.jsonl") * 2
# --- the DESIGN SOUL (one grammar of beauty: art+architecture+nature+cosmos+craft) ---
rows += load("architecture_design.jsonl") * 2      # the architect's eye (35)
rows += load("nature_cosmos_design.jsonl") * 2     # nature/math/cosmos grammar (36)
rows += load("design_soul.jsonl") * 2              # type/color/motion/perception/taste (37)
rows += load("creative_coding.jsonl") * 5          # generative-art gold exemplars (31), few -> weight up
rows += load("callsieve_protocol.jsonl") * 3       # callsieve-first zero-token tool use (28)
rows += load("db_testing.jsonl")                   # already x3 on disk
rows += load("stack_complete.jsonl")               # already x2 on disk
rows += load("ts7_preference.jsonl") * 3
swe = load("swe_agentic.jsonl")
rows += swe
rows += load("agentic_loops.jsonl") * 3            # real edit->check->fix loops (42)
# --- public function-completions: CAP so they don't drown the mix ---
ver = load("verified.jsonl")
random.shuffle(ver)
rows += ver[:8000]
print(f"  mine+niche+verified(capped): {len(rows)} (swe_agentic={len(swe)})")

# --- agentic + reasoning + anti-forgetting from HF ---
try:
    from datasets import load_dataset

    def pull_msgs(dsid, n, config=None, split="train"):
        """Robust: handles messages/conversations format AND field-pair formats."""
        got = 0
        try:
            ds = (load_dataset(dsid, config, split=split, streaming=True)
                  if config else load_dataset(dsid, split=split, streaming=True))
            for ex in ds:
                if got >= n:
                    break
                m = ex.get("messages") or ex.get("conversations")
                if isinstance(m, list) and len(m) >= 2:
                    mm = [{"role": x.get("role", x.get("from", "user")),
                           "content": str(x.get("content", x.get("value", "")))[:6000]}
                          for x in m if isinstance(x, dict)][:8]
                    if len(mm) >= 2:
                        rows.append({"messages": mm}); got += 1
                        continue
                # field-pair fallback
                for uf, af in [("problem", "solution"), ("question", "answer"),
                               ("query", "response"), ("prompt", "completion")]:
                    u, a = ex.get(uf), ex.get(af)
                    if isinstance(u, str) and a:
                        rows.append({"messages": [
                            {"role": "user", "content": u},
                            {"role": "assistant", "content": str(a)[:6000]}]})
                        got += 1
                        break
            print(f"  +{got} from {dsid}" + (f" [{config}]" if config else ""))
        except Exception as e:  # noqa: BLE001
            print(f"  [skip] {dsid}: {str(e)[:60]}")

    # reasoning over code (Mixture-of-Thoughts needs a config; 'code' fits our niche)
    pull_msgs("open-r1/Mixture-of-Thoughts", 8000, config="code")
    # agentic tool-use trajectories (SWE-smith split is 'tool', not 'train')
    if not swe:
        pull_msgs("SWE-bench/SWE-smith-trajectories", 4000, split="tool")
        pull_msgs("glaiveai/glaive-function-calling-v2", 3000)   # tool-calling backup
    # anti-forgetting general (ultrachat messages format)
    try:
        ds = load_dataset("HuggingFaceH4/ultrachat_200k", split="train_sft",
                          streaming=True)
        g = 0
        for ex in ds:
            if g >= 6000:
                break
            m = ex.get("messages")
            if isinstance(m, list) and len(m) >= 2:
                rows.append({"messages": m[:2]})
                g += 1
        print(f"  +{g} anti-forgetting (ultrachat)")
    except Exception as e:  # noqa: BLE001
        print(f"  [skip] ultrachat: {str(e)[:50]}")
except Exception as e:  # noqa: BLE001
    print(f"  [warn] datasets unavailable: {e}")

random.shuffle(rows)
nv = max(50, len(rows) // 40)
os.makedirs(os.path.join(ROOT, "heal", "data"), exist_ok=True)
for name, d in [("valid", rows[:nv]), ("train", rows[nv:])]:
    with open(os.path.join(ROOT, "heal", "data", f"{name}.jsonl"), "w") as f:
        f.write("\n".join(json.dumps(r) for r in d))
print(f"\n  BALANCED heal/data: {len(rows)-nv} train / {nv} valid")
