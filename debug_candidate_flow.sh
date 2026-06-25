#!/usr/bin/env bash
set -euo pipefail

export KB_SEARCH_API_KEY=dev_change_me

# 1. sync source
  make sync-kaiyuan-source

# 2. generate downstream candidate
make generate-candidate

# 3. copy to upstream inbox
mkdir -p apps/local-kb-unified/incoming/downstream_candidates/codex-ready
rsync -av \
  apps/star-omen/data/generated_candidates/extract_cards/kaiyuan_zhanjing/ \
  apps/local-kb-unified/incoming/downstream_candidates/codex-ready/

# 4. validate upstream
make validate-candidates

echo
echo "下一步：手动编辑 apps/local-kb-unified/incoming/downstream_candidates/codex-ready/*.md"
echo "把某条 review_status: pending 改成 review_status: approved"
echo "然后运行：make promote-candidates && make ingest && make sync"