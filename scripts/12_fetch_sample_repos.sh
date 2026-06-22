#!/usr/bin/env bash
# Fetch small, real public repos across the target stack to TEST the RAG layer.
# Shallow clones (--depth 1) to keep it fast. Swap these for your own repos
# in production via:  python scripts/10_rag_index.py --repos ~/code/yourproj
set -euo pipefail
cd "$(dirname "$0")/.."
DEST="rag/sample_repos"
mkdir -p "$DEST"

# repo -> language coverage (kept small on purpose)
REPOS=(
  "https://github.com/pallets/click"        # python   (CLI framework)
  "https://github.com/sindresorhus/ky"      # typescript/js (HTTP client)
  "https://github.com/rust-lang/log"        # rust     (logging facade)
  "https://github.com/gorilla/mux"          # go       (HTTP router)
)

for url in "${REPOS[@]}"; do
  name="$(basename "$url")"
  if [ -d "$DEST/$name" ]; then
    echo ">> $name already present, skipping"
  else
    echo ">> Cloning $name ..."
    git clone --depth 1 --quiet "$url" "$DEST/$name"
  fi
done

echo ">> Sample repos in $DEST:"
du -sh "$DEST"/* 2>/dev/null || true
echo ">> Index them:  python scripts/10_rag_index.py --repos $DEST --out rag/index"
