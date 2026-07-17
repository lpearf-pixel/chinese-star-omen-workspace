#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
set -a
# shellcheck source=/dev/null
source "$ROOT_DIR/.env"
set +a

PORT="${KB_SEARCH_API_PORT:-8008}"
KEY="${KB_SEARCH_API_KEY:?KB_SEARCH_API_KEY missing in .env}"
COLLECTION="${KB_SEARCH_DEFAULT_COLLECTION:-local_kb_kaiyuan_v2}"
BASE="http://127.0.0.1:${PORT}"

pretty_json() {
  if command -v jq >/dev/null 2>&1; then
    jq .
  else
    python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))'
  fi
}

retrieve() {
  local name="$1"
  local body="$2"
  echo "======== ${name} ========"
  response="$(curl -sS -w "\n%{http_code}" "${BASE}/v1/retrieve" \
    -H "Authorization: Bearer ${KEY}" \
    -H "Content-Type: application/json" \
    -d "${body}")"
  code="$(echo "${response}" | tail -n1)"
  body_out="$(echo "${response}" | sed '$d')"
  echo "HTTP ${code}"
  echo "${body_out}" | pretty_json
  [[ "$code" == "200" ]]
}

curl -fsS "${BASE}/v1/health" | pretty_json
retrieve "Kaiyuan evidence" "{\"query\":\"荧惑守心\",\"top_k\":5,\"collection\":\"${COLLECTION}\",\"query_mode\":\"evidence\",\"literal_first\":true,\"filters\":{\"kb_book_id\":\"kaiyuan_zhanjing\"}}"
