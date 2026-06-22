"""#23 — REAP calibration mix (Cerebras ICLR-2026) for the NEXT prune. Streams + samples the composite set;
CPU/network/disk, memory-light. NOTE: xlam-function-calling is GATED — request access on HF first, else it
skips. The saliency fix (renormalize top-k router logits to sum=1, ~+0.7pp) goes in the prune (scripts/02_*).

  python scripts/prep_reap_calib.py --dry-run
  python scripts/prep_reap_calib.py --out calib/reap_mix.jsonl
"""
import argparse
import json
import os

# (dataset, config, split, n, role) — config/split fixed per the actual HF dataset
MIX = [
    ("theblackcat102/evol-codealpaca-v1", None, "train", 4096, "general coding"),
    ("open-r1/Mixture-of-Thoughts", "all", "train", 12288, "reasoning (code/math/science)"),
    ("Salesforce/xlam-function-calling-60k", None, "train", 4096, "tool calling (GATED — request HF access)"),
    ("SWE-bench/SWE-smith-trajectories", None, "tool", 4096, "agentic / multi-turn"),
]
MAX_SEQ = 16384


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="calib/reap_mix.jsonl")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    print(f"  REAP calib mix (Cerebras, ICLR-2026): {sum(m[3] for m in MIX)} samples @ {MAX_SEQ} tok")
    for ds, cfg, split, n, role in MIX:
        print(f"    {n:6}  {ds:42} [{cfg or '-'}/{split}] {role}")
    print("  + saliency fix: renormalize top-k router logits to sum=1 (~+0.7pp) — apply in the prune")
    if a.dry_run:
        return
    from datasets import load_dataset
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    kept = 0
    with open(a.out, "w") as w:
        for ds, cfg, split, n, role in MIX:
            try:
                d = (load_dataset(ds, cfg, split=split, streaming=True) if cfg
                     else load_dataset(ds, split=split, streaming=True))
                got = 0
                for ex in d:
                    if got >= n:
                        break
                    w.write(json.dumps({"source": ds, "role": role, "text": str(ex)[:MAX_SEQ * 4]}) + "\n")
                    got, kept = got + 1, kept + 1
                print(f"    sampled {got} from {ds}")
            except Exception as e:
                print(f"    SKIP {ds}: {str(e)[:70]}")
    print(f"  wrote {kept}/{sum(m[3] for m in MIX)} calib samples -> {a.out}")


if __name__ == "__main__":
    main()
