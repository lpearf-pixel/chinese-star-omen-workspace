SHELL := /bin/bash
ROOT := $(shell pwd)
INDEX_PY := $(ROOT)/index-jobs/.venv/bin/python
COLLECTION ?= $${KB_SEARCH_DEFAULT_COLLECTION:-local_kb_kaiyuan_v2}

.PHONY: setup up down logs ps restart rebuild pull-models health kb-search ingest ingest-full ingest-recreate ingest-dry-run test validate-candidates promote-candidates corpus-manifest release-drill capture-release-observation

setup:
	bash $(ROOT)/index-jobs/setup_env.sh

up:
	docker compose --env-file $(ROOT)/.env -f $(ROOT)/docker-compose.yml up -d

down:
	docker compose --env-file $(ROOT)/.env -f $(ROOT)/docker-compose.yml down

restart:
	docker compose --env-file $(ROOT)/.env -f $(ROOT)/docker-compose.yml down
	docker compose --env-file $(ROOT)/.env -f $(ROOT)/docker-compose.yml up -d

rebuild:
	docker compose --env-file $(ROOT)/.env -f $(ROOT)/docker-compose.yml down --remove-orphans
	docker compose --env-file $(ROOT)/.env -f $(ROOT)/docker-compose.yml build --no-cache kb-search
	docker compose --env-file $(ROOT)/.env -f $(ROOT)/docker-compose.yml up -d

logs:
	docker compose --env-file $(ROOT)/.env -f $(ROOT)/docker-compose.yml logs -f --tail=150

ps:
	docker compose --env-file $(ROOT)/.env -f $(ROOT)/docker-compose.yml ps

pull-models:
	bash $(ROOT)/scripts/init_models.sh

health:
	bash $(ROOT)/scripts/healthcheck.sh

kb-search:
	docker compose --env-file $(ROOT)/.env -f $(ROOT)/docker-compose.yml up -d --build kb-search

# Default: skip unchanged managed points, upsert changed/new passages, delete stale managed points after success.
ingest:
	cd $(ROOT)/index-jobs && $(INDEX_PY) ingest.py --mode incremental --collection "$(COLLECTION)"

# Re-embed every desired managed point without deleting the collection first.
ingest-full:
	cd $(ROOT)/index-jobs && $(INDEX_PY) ingest.py --mode full --collection "$(COLLECTION)"

# Destructive recreation is always explicit.
ingest-recreate:
	cd $(ROOT)/index-jobs && $(INDEX_PY) ingest.py --mode full --collection "$(COLLECTION)" --recreate

ingest-dry-run:
	cd $(ROOT)/index-jobs && $(INDEX_PY) ingest.py --mode incremental --collection "$(COLLECTION)" --dry-run

corpus-manifest:
	python scripts/corpus_manifest.py --collection "$(COLLECTION)" --out data/corpus_manifest.json

release-drill:
	python scripts/verify_release_drill.py --input tests/fixtures/release_drill_v1.json

capture-release-observation:
	@test -n "$(PHASE)" -a -n "$(ACTIVE_COLLECTION)" -a -n "$(QUERY)" -a -n "$(BASE_URL)" -a -n "$(QDRANT_URL)" -a -n "$(API_KEY_ENV)" -a -n "$(OUT)" || { echo "required: PHASE ACTIVE_COLLECTION QUERY BASE_URL QDRANT_URL API_KEY_ENV OUT" >&2; exit 2; }
	python scripts/capture_release_observation.py --phase "$(PHASE)" --active-collection "$(ACTIVE_COLLECTION)" --query "$(QUERY)" --base-url "$(BASE_URL)" --qdrant-url "$(QDRANT_URL)" --api-key-env "$(API_KEY_ENV)" --out "$(OUT)"

validate-candidates:
	python scripts/import_candidate_cards.py --inbox incoming/downstream_candidates/codex-ready --book-id kaiyuan_zhanjing --mode validate

promote-candidates:
	python scripts/import_candidate_cards.py --inbox incoming/downstream_candidates/codex-ready --book-id kaiyuan_zhanjing --mode promote

test:
	PYTHONPATH=.:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q
