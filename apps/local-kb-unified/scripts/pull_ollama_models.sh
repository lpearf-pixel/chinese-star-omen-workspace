#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT_DIR/.env"

pull_one() {
  local model="$1"
  [[ -z "$model" ]] && return 0
  echo ">>> ollama pull $model"
  ollama pull "$model"
}

if ! command -v ollama >/dev/null 2>&1; then
  echo "error: host ollama command not found; install https://ollama.com first" >&2
  exit 1
fi

if [[ $# -gt 0 ]]; then
  for model in "$@"; do
    pull_one "$model"
  done
else
  pull_one "$CHAT_MODEL"
  pull_one "$EMBED_MODEL"
  for model in ${OLLAMA_EXTRA_MODELS:-}; do
    pull_one "$model"
  done
fi

ollama list
