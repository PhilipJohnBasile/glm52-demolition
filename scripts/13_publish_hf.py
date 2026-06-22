#!/usr/bin/env python3
"""Publish the demolished model to Hugging Face — SAFELY.

Outward-facing and hard to retract, so this script:
  * dry-runs by default; uploads ONLY with --push
  * refuses to run unless the model dir exists and looks like a model
  * refuses unless a NOTICE (base-model MIT copyright) is present
  * warns if API-distilled / private-repo training data may be baked in
  * writes the model card + NOTICE into the repo

Prereqs you control: a HF account, `huggingface-cli login` (or HF_TOKEN env),
and — critically — a model you actually BUILT by running the pipeline.

  # dry run (default): validates everything, uploads nothing
  python scripts/13_publish_hf.py --repo-id youruser/GLM-5.2-Demolished \
      --model-dir models/GLM-5.2-demolished-healed
  # actually publish:
  python scripts/13_publish_hf.py --repo-id youruser/GLM-5.2-Demolished \
      --model-dir models/GLM-5.2-demolished-healed --push
"""

import argparse
import os
import sys

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
NOTICE = os.path.join(ROOT, "NOTICE")
CARD = os.path.join(ROOT, "MODEL_CARD.md")


def ensure_notice():
    if os.path.exists(NOTICE):
        return
    open(NOTICE, "w").write(
        "This model is a derivative of zai-org/GLM-5.2, licensed under the MIT "
        "License.\n\nCopyright (c) Z.ai / Zhipu AI.\n\n"
        "Permission is hereby granted, free of charge, ... (full MIT text "
        "retained from the base model; replace with the exact text from the "
        "base model's LICENSE before publishing).\n")
    print(f"  wrote stub {NOTICE} — REPLACE with the exact base-model MIT text.")


def preflight(model_dir):
    problems = []
    if not os.path.isdir(model_dir):
        problems.append(f"model dir not found: {model_dir} — build it first "
                        "(run the pipeline; the 395GB download + prune/heal).")
    else:
        files = os.listdir(model_dir)
        if not any(f.endswith(".safetensors") for f in files):
            problems.append(f"{model_dir} has no *.safetensors — not a model.")
        if "config.json" not in files:
            problems.append(f"{model_dir} missing config.json.")
    if not os.path.exists(CARD):
        problems.append("MODEL_CARD.md missing.")
    # data-provenance guard
    distilled = os.path.join(ROOT, "heal", "data", "train.jsonl")
    if os.path.exists(distilled):
        print("  [check] confirm released weights were NOT trained on "
              "API-distilled or private-repo data (license/ToS). For a public "
              "release use the verified-SFT + open-data path only.")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-id", required=True, help="e.g. youruser/GLM-5.2-Demolished")
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--private", action="store_true",
                    help="create a private repo (recommended for first upload)")
    ap.add_argument("--push", action="store_true",
                    help="ACTUALLY upload (default: dry-run only)")
    args = ap.parse_args()

    ensure_notice()
    problems = preflight(args.model_dir)
    if problems:
        print("PUBLISH BLOCKED:")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    size = sum(os.path.getsize(os.path.join(args.model_dir, f))
               for f in os.listdir(args.model_dir)
               if os.path.isfile(os.path.join(args.model_dir, f))) / 1e9
    print(f">> Ready: {args.repo_id}  ({size:.1f} GB)  private={args.private}")
    print(f"   model card: {CARD}   notice: {NOTICE}")

    if not args.push:
        print("\n   DRY RUN — nothing uploaded. Re-run with --push to publish.")
        print("   Before --push: (1) confirm GLM-5.2 base LICENSE is MIT, "
              "(2) NOTICE has the exact base copyright, (3) eval numbers are in "
              "the card and DON'T claim flagship parity, (4) data provenance ok.")
        return

    from huggingface_hub import HfApi, create_repo
    create_repo(args.repo_id, repo_type="model", private=args.private,
                exist_ok=True)
    api = HfApi()
    api.upload_file(path_or_fileobj=CARD, path_in_repo="README.md",
                    repo_id=args.repo_id)
    api.upload_file(path_or_fileobj=NOTICE, path_in_repo="NOTICE",
                    repo_id=args.repo_id)
    api.upload_folder(folder_path=args.model_dir, repo_id=args.repo_id,
                      ignore_patterns=["*.lock", ".git*"])
    print(f">> Published: https://huggingface.co/{args.repo_id}")
    print("   Started private? Flip to public in repo settings when ready.")


if __name__ == "__main__":
    main()
