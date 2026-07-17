SHELL := /bin/bash
ROOT := $(shell pwd)
INDEX_PY := $(ROOT)/index-jobs/.venv/bin/python
COLLECTION ?= $${KB_SEARCH_DEFAULT_COLLECTION:-local_kb_kaiyuan_v2}

.PHONY: setup up down logs ps restart rebuild pull-models health kb-search ingest ingest-recreate ingest-dry-run test validate-candidates promote-candidates corpus-manifest

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

# Non-destructive default: import/upsert into the trial collection without deleting it.
ingest:
	cd $(ROOT)/index-jobs && $(INDEX_PY) ingest.py --mode full --collection "$(COLLECTION)"

# Destructive recreation is always explicit.
ingest-recreate:
	cd $(ROOT)/index-jobs && $(INDEX_PY) ingest.py --mode full --collection "$(COLLECTION)" --recreate

ingest-dry-run:
	cd $(ROOT)/index-jobs && $(INDEX_PY) ingest.py --mode full --collection "$(COLLECTION)" --dry-run

corpus-manifest:
	python scripts/corpus_manifest.py --collection "$(COLLECTION)" --out data/corpus_manifest.json

validate-candidates:
	python scripts/import_candidate_cards.py --inbox incoming/downstream_candidates/codex-ready --book-id kaiyuan_zhanjing --mode validate

promote-candidates:
	python scripts/import_candidate_cards.py --inbox incoming/downstream_candidates/codex-ready --book-id kaiyuan_zhanjing --mode promote

test:
	PYTHONPATH=.:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q
