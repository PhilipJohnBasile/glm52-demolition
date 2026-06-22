#!/usr/bin/env python3
"""Publish the demolished model to Hugging Face. Uploads the model card as the repo
README plus the chosen artifacts. Needs auth first: `hf auth login` (or set HF_TOKEN).

Tiers (smallest, most useful first):
  patches  — the model card + dist/ engine patches (anyone can load GLM-5.2 in mlx_lm). ~MB
  adapters — + the SFT/GRPO LoRA adapters (apply on your own quant).                    ~GB
  model    — + the full 99GB quantized model.                                           99GB
  all      — everything.

  python scripts/48_publish_hf.py --repo <user>/GLM-5.2-Demolition-q3a4 --what patches
  python scripts/48_publish_hf.py --repo <user>/GLM-5.2-Demolition-q3a4 --what all --private
"""
import argparse
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="<user>/<name> on Hugging Face")
    ap.add_argument("--what", choices=["patches", "adapters", "model", "all"], default="patches")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--private", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    from huggingface_hub import HfApi, create_repo, upload_file, upload_folder
    api = HfApi()
    if not (os.environ.get("HF_TOKEN") or api.token):
        raise SystemExit("  no HF auth — run `hf auth login` or set HF_TOKEN first.")
    plan = [("dist/MODEL_CARD.md", "README.md", "model card -> README")]
    if args.what in ("patches", "all"):
        plan.append(("dist", "dist", "engine patches + installer (no weights)"))
    if args.what in ("adapters", "all"):
        import glob as _glob
        for a in sorted(_glob.glob("heal/adapters-*")):
            if os.path.isdir(a) and "sound" not in os.path.basename(a):   # skip the flywheel-bugged sound throwaway
                plan.append((a, a, f"LoRA soul {os.path.basename(a)}"))
    if args.what in ("model", "all"):
        plan.append((args.model, ".", f"FULL model {args.model} (99GB — slow upload)"))
    print(f"  repo: {args.repo} ({'private' if args.private else 'public'})")
    for src, dst, desc in plan:
        print(f"    {'WOULD upload' if args.dry_run else 'upload'}: {src} -> {dst}  ({desc})")
    if args.dry_run:
        return
    create_repo(args.repo, exist_ok=True, private=args.private)
    for src, dst, _ in plan:
        if os.path.isdir(src):
            upload_folder(folder_path=src, path_in_repo=dst, repo_id=args.repo,
                          ignore_patterns=["*.bak", "*.orig", "__pycache__*", "*_adapters.safetensors"])
        else:
            upload_file(path_or_fileobj=src, path_in_repo=dst, repo_id=args.repo)
    print(f"  ✅ published -> https://huggingface.co/{args.repo}")


if __name__ == "__main__":
    main()
