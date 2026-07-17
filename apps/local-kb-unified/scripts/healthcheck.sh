#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing $ENV_FILE; copy .env.example to .env and configure local secrets" >&2
  exit 2
fi

set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

failures=0
check_http() {
  local name="$1"
  local url="$2"
  printf '%s: ' "$name"
  if curl -fsS --max-time 10 "$url" >/dev/null; then
    echo ok
  else
    echo not-ready
    failures=$((failures + 1))
  fi
}

check_http "OpenWebUI" "http://127.0.0.1:${OPENWEBUI_PORT:-3000}"
check_http "Ollama" "http://127.0.0.1:${OLLAMA_PORT:-11434}/api/tags"
check_http "Qdrant" "http://127.0.0.1:${QDRANT_HTTP_PORT:-6333}/healthz"

printf 'PostgreSQL: '
if docker exec local-kb-postgres pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
  echo ok
else
  echo not-ready
  failures=$((failures + 1))
fi

check_http "KB Search API" "http://127.0.0.1:${KB_SEARCH_API_PORT:-8008}/v1/health"

exit "$failures"
