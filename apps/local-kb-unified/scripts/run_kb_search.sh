#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/kb-search"

PORT="${KB_SEARCH_API_PORT:-8008}"
PYTHON="${PYTHON:-python3}"

if [[ ! -d .venv ]]; then
  "$PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install -q -U pip
.venv/bin/python -m pip install -q -r requirements.txt

exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
