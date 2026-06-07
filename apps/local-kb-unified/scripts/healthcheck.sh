#!/usr/bin/env bash
set -euo pipefail
python scripts/corpus_manifest.py --out data/corpus_manifest.json >/dev/null
echo "ok"
