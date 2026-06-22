#!/usr/bin/env bash
# Curated, 2026-active, latest-version repos per target language — high-quality
# idiomatic code to train/RAG the demolished agentic model on modern conventions.
# Researched + version-verified June 2026 (dates noted). Shallow clones.
#
# After fetching:
#   python scripts/10_rag_index.py --repos rag/training_repos --out rag/index
#   python scripts/06b_verified_sft.py --gen none --repos rag/training_repos
set -euo pipefail
cd "$(dirname "$0")/.."
DEST="rag/training_repos"
mkdir -p "$DEST"

# repo|subdir — chosen for idiomatic modern code + active 2026 maintenance
REPOS=(
  # --- Python 3.13+, modern typing/async ---
  "https://github.com/fastapi/fastapi"          # v0.137.1 Jun-2026, async+typed
  "https://github.com/pydantic/pydantic"        # modern typing core
  "https://github.com/Textualize/textual"       # reactive modern Python

  # --- TypeScript 6/7 (current June 2026), strict, web standards ---
  "https://github.com/honojs/hono"              # v4.12.25 Jun-2026, 99.5% TS
  "https://github.com/trpc/trpc"                # advanced TS types, full-stack
  "https://github.com/toss/es-toolkit"          # modern 2026 JS/TS utilities

  # --- JavaScript modern ESM ---
  "https://github.com/sindresorhus/ky"          # gold-standard modern ESM

  # --- Rust edition 2024 ---
  "https://github.com/ratatui/ratatui"          # v0.30.1 Jun-2026
  "https://github.com/starship/starship"        # idiomatic, very active

  # --- Go 1.2x, generics, stdlib-idiomatic ---
  "https://github.com/go-chi/chi"               # v5.3.0 May-2026, stdlib-only
  "https://github.com/gin-gonic/gin"            # most-active Go web framework

  # --- HTML / CSS (real .css/.scss/.html, modern) ---
  "https://github.com/saadeghi/daisyui"         # active CSS component lib
  "https://github.com/picocss/pico"             # semantic HTML+SCSS (v2.1.1)
  "https://github.com/markmead/hyperui"         # modern HTML components
)

for url in "${REPOS[@]}"; do
  name="$(basename "$url")"
  if [ -d "$DEST/$name" ]; then echo ">> $name present, skip"; continue; fi
  echo ">> cloning $name ..."
  git clone --depth 1 --quiet "$url" "$DEST/$name" || echo "   [warn] failed: $url"
done

echo ">> training repos in $DEST:"; du -sh "$DEST"/* 2>/dev/null | sort -h | tail -20
echo ">> next: index for RAG + ingest for verified-SFT (see header)."
