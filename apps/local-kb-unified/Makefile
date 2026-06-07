.PHONY: up kb-search ingest health test

up:
	@echo "Local-KB-Unified services are managed by docker compose in full installations."

kb-search:
	@echo "Run kb-search with: uvicorn kb_search.app:app --host 0.0.0.0 --port $${KB_SEARCH_API_PORT:-8008}"

ingest:
	python scripts/corpus_manifest.py --collection $${KB_SEARCH_DEFAULT_COLLECTION:-star_omen_kb} --out data/corpus_manifest.json
	@echo "ingest smoke complete: scanned data/sources and approved/official data/generated only; incoming/downstream_candidates excluded"

health:
	bash scripts/healthcheck.sh

test:
	PYTHONPATH=.:../../packages/kb-contracts/python pytest -q
