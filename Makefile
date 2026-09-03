UPSTREAM_DIR=apps/local-kb-unified
DOWNSTREAM_DIR=apps/star-omen
PYTHON?=python3

.PHONY: status up kb-search ingest health b9-preview vfl-s0-run vfl-s1-run sync-kaiyuan-source inspect-kaiyuan validate-candidates promote-candidates generate-candidate sync downstream-test upstream-test contracts-test text-core-test audit-kaiyuan-corpus audit-kaiyuan-baseline compare-kaiyuan-volumes release-drill capture-release-observation assemble-release-artifact create-release-evidence-bundle verify-release-evidence-bundle

status:
	git status --short

up:
	cd $(UPSTREAM_DIR) && make up

kb-search:
	cd $(UPSTREAM_DIR) && make kb-search

ingest:
	cd $(UPSTREAM_DIR) && make ingest

health:
	cd $(UPSTREAM_DIR) && bash scripts/healthcheck.sh

b9-preview:
	@test -n "$(B9_OUTPUT_DIR)" || { \
	  printf 'B9_OUTPUT_DIR is required\n' >&2; \
	  exit 2; \
	}
	B9_FFMPEG_BIN="$(B9_FFMPEG_BIN)" \
	B9_FFPROBE_BIN="$(B9_FFPROBE_BIN)" \
	$(PYTHON) scripts/b9_preview.py --package-dir "$(B9_OUTPUT_DIR)"

unexport VFL_AUDIT VFL_PROBES VFL_OUTPUT VFL_OUTCOME
vfl-s0-run: private override export VFL_S0_AUDIT_PATH := $(value VFL_AUDIT)
vfl-s0-run: private override export VFL_S0_PROBES_PATH := $(value VFL_PROBES)
vfl-s0-run: private override export VFL_S0_OUTPUT_PATH := $(value VFL_OUTPUT)
vfl-s0-run: private override export VFL_S0_OUTCOME_PATH := $(value VFL_OUTCOME)
vfl-s0-run:
	@test -n "$${VFL_S0_AUDIT_PATH}" || { \
	  printf 'VFL_AUDIT is required\n' >&2; \
	  exit 2; \
	}
	@test -n "$${VFL_S0_PROBES_PATH}" || { \
	  printf 'VFL_PROBES is required\n' >&2; \
	  exit 2; \
	}
	@test -n "$${VFL_S0_OUTPUT_PATH}" || { \
	  printf 'VFL_OUTPUT is required\n' >&2; \
	  exit 2; \
	}
	@set -- \
	  --audit "$${VFL_S0_AUDIT_PATH}" \
	  --probes "$${VFL_S0_PROBES_PATH}" \
	  --output "$${VFL_S0_OUTPUT_PATH}"; \
	if test -n "$${VFL_S0_OUTCOME_PATH}"; then \
	  set -- "$$@" --outcome "$${VFL_S0_OUTCOME_PATH}"; \
	fi; \
	PYTHONPATH=$(DOWNSTREAM_DIR):packages/kb-contracts/python:packages/kb-text-core/python \
	$(PYTHON) $(DOWNSTREAM_DIR)/scripts/run_video_feedback_loop.py "$$@"

unexport VFL_S1_AUDIT VFL_S1_QUERY_PLAN VFL_S1_KB_ROOT VFL_S1_SOURCE_SNAPSHOT VFL_S1_OUTPUT
vfl-s1-run: private override export VFL_S1_AUDIT_PATH := $(value VFL_S1_AUDIT)
vfl-s1-run: private override export VFL_S1_QUERY_PLAN_PATH := $(value VFL_S1_QUERY_PLAN)
vfl-s1-run: private override export VFL_S1_KB_ROOT_PATH := $(value VFL_S1_KB_ROOT)
vfl-s1-run: private override export VFL_S1_SOURCE_SNAPSHOT_PATH := $(value VFL_S1_SOURCE_SNAPSHOT)
vfl-s1-run: private override export VFL_S1_OUTPUT_PATH := $(value VFL_S1_OUTPUT)
vfl-s1-run:
	@test -n "$${VFL_S1_AUDIT_PATH}" || { \
	  printf 'VFL_S1_AUDIT is required\n' >&2; \
	  exit 2; \
	}
	@test -n "$${VFL_S1_QUERY_PLAN_PATH}" || { \
	  printf 'VFL_S1_QUERY_PLAN is required\n' >&2; \
	  exit 2; \
	}
	@test -n "$${VFL_S1_KB_ROOT_PATH}" || { \
	  printf 'VFL_S1_KB_ROOT is required\n' >&2; \
	  exit 2; \
	}
	@test -n "$${VFL_S1_SOURCE_SNAPSHOT_PATH}" || { \
	  printf 'VFL_S1_SOURCE_SNAPSHOT is required\n' >&2; \
	  exit 2; \
	}
	@test -n "$${VFL_S1_OUTPUT_PATH}" || { \
	  printf 'VFL_S1_OUTPUT is required\n' >&2; \
	  exit 2; \
	}
	@set -- \
	  --audit "$${VFL_S1_AUDIT_PATH}" \
	  --query-plan "$${VFL_S1_QUERY_PLAN_PATH}" \
	  --kb-root "$${VFL_S1_KB_ROOT_PATH}" \
	  --source-snapshot "$${VFL_S1_SOURCE_SNAPSHOT_PATH}" \
	  --output "$${VFL_S1_OUTPUT_PATH}"; \
	PYTHONPATH=$(DOWNSTREAM_DIR):packages/kb-contracts/python:packages/kb-text-core/python \
	$(PYTHON) $(DOWNSTREAM_DIR)/scripts/run_video_feedback_loop_s1.py "$$@"

sync-kaiyuan-source:
	python scripts/sync_kaiyuan_source.py $(if $(KAIYUAN_SOURCE_DIR),--source-dir "$(KAIYUAN_SOURCE_DIR)",) --clean

inspect-kaiyuan:
	cd $(DOWNSTREAM_DIR) && PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python python -m src.cli inspect-kb \
	  --query "荧惑守心" \
	  --book-id kaiyuan_zhanjing \
	  --query-mode evidence \
	  --literal-first \
	  --limit 8 \
	  --show-raw

validate-candidates:
	cd $(UPSTREAM_DIR) && python scripts/import_candidate_cards.py \
	  --inbox incoming/downstream_candidates/codex-ready \
	  --book-id kaiyuan_zhanjing \
	  --mode validate

promote-candidates:
	cd $(UPSTREAM_DIR) && python scripts/import_candidate_cards.py \
	  --inbox incoming/downstream_candidates/codex-ready \
	  --book-id kaiyuan_zhanjing \
	  --mode promote

generate-candidate:
	cd $(DOWNSTREAM_DIR) && PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python python -m src.cli generate-candidate-card \
	  --query "荧惑守心" \
	  --book-id kaiyuan_zhanjing \
	  --out-dir data/generated_candidates/extract_cards/kaiyuan_zhanjing

sync:
	cd $(DOWNSTREAM_DIR) && python -m src.cli sync-upstream-status \
	  --book-id kaiyuan_zhanjing \
	  --candidate-root data/generated_candidates \
	  --base-url http://127.0.0.1:8008

downstream-test:
	cd $(DOWNSTREAM_DIR) && PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q

upstream-test:
	cd $(UPSTREAM_DIR) && PYTHONPATH=.:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q

release-drill:
	cd $(UPSTREAM_DIR) && python scripts/verify_release_drill.py --input tests/fixtures/release_drill_v1.json

capture-release-observation:
	$(MAKE) -C $(UPSTREAM_DIR) capture-release-observation PHASE="$(PHASE)" ACTIVE_COLLECTION="$(ACTIVE_COLLECTION)" QUERY="$(QUERY)" BASE_URL="$(BASE_URL)" QDRANT_URL="$(QDRANT_URL)" API_KEY_ENV="$(API_KEY_ENV)" OUT="$(OUT)"

assemble-release-artifact:
	$(MAKE) -C $(UPSTREAM_DIR) assemble-release-artifact BEFORE_SWITCH="$(BEFORE_SWITCH)" AFTER_SWITCH="$(AFTER_SWITCH)" AFTER_ROLLBACK="$(AFTER_ROLLBACK)" EXPECTED_MANIFEST="$(EXPECTED_MANIFEST)" OUT="$(OUT)"

create-release-evidence-bundle:
	$(MAKE) -C $(UPSTREAM_DIR) create-release-evidence-bundle BEFORE_SWITCH="$(BEFORE_SWITCH)" AFTER_SWITCH="$(AFTER_SWITCH)" AFTER_ROLLBACK="$(AFTER_ROLLBACK)" EXPECTED_MANIFEST="$(EXPECTED_MANIFEST)" ASSEMBLED_INPUT="$(ASSEMBLED_INPUT)" RELEASE_HEAD="$(RELEASE_HEAD)" CREATED_AT="$(CREATED_AT)" OUT="$(OUT)"

verify-release-evidence-bundle:
	$(MAKE) -C $(UPSTREAM_DIR) verify-release-evidence-bundle BUNDLE="$(BUNDLE)"

contracts-test:
	PYTHONPATH=packages/kb-contracts/python pytest -q packages/kb-contracts/tests

text-core-test:
	PYTHONPATH=packages/kb-text-core/python pytest -q packages/kb-text-core/tests

audit-kaiyuan-corpus:
	PYTHONPATH=packages/kb-text-core/python python scripts/audit_kaiyuan_corpus.py \
	  --fulltext "$(UPSTREAM_DIR)/data/sources/古籍/唐開元占經/唐開元占經-全文合併版.md" \
	  --volumes-dir "$(UPSTREAM_DIR)/data/sources/古籍/唐開元占經/分卷" \
	  --out "$(UPSTREAM_DIR)/data/reports/kaiyuan_zhanjing/corpus_audit.json" \
	  --strict

audit-kaiyuan-baseline:
	PYTHONPATH=packages/kb-text-core/python python scripts/audit_kaiyuan_baseline.py \
	  --fulltext "$(UPSTREAM_DIR)/data/sources/古籍/唐開元占經/唐開元占經-全文合併版.md" \
	  --volumes-dir "$(UPSTREAM_DIR)/data/sources/古籍/唐開元占經/分卷" \
	  --baseline corpus/kaiyuan_zhanjing/baseline.json

compare-kaiyuan-volumes:
	PYTHONPATH=packages/kb-text-core/python python scripts/compare_kaiyuan_volumes.py --strict
