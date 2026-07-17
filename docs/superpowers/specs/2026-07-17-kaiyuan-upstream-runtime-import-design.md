# Kaiyuan Upstream Runtime Import Design

## Goal

Replace the monorepo's minimal Local-KB-Unified scaffold with the real, sanitized runtime supplied from `/Users/kandysmith/local-kb-unified`, while preserving the candidate-card workflow and keeping all release work on `stable/kaiyuan-v2` rather than `main`.

## Source Baseline

- Source repository: `lpearf-pixel/Local-KB-Unified`
- Source branch: `main`
- Recorded source HEAD: `62cb52f314a8424713a605bda2fb6dab3c5bdbb5`
- Runtime archive SHA-256: `1b8d26df4ebbbdeff3a02c6cbf672cfba0ad086bf629b4bcf29439d7a76023de`
- Snapshot path at collection time: `/Users/kandysmith/local-kb-unified`

The source worktree contained substantial untracked runtime code, so this import is treated as an explicit reviewed snapshot rather than a subtree pull.

## Scope

B1 imports and sanitizes:

- Docker Compose service definitions for Qdrant, PostgreSQL, KB Search and OpenWebUI;
- the real `kb-search` FastAPI service;
- real `index-jobs` ingestion and source adapters;
- operational scripts and selected runtime documentation;
- safe environment templates and ignore rules;
- upstream unit tests and CI smoke gates.

B1 preserves:

- `scripts/import_candidate_cards.py`;
- `scripts/corpus_manifest.py` and corpus metadata contracts;
- existing `data/sources`, `data/generated` and incoming candidate boundaries;
- all shared packages under `packages/`.

## Safety Decisions

1. `main` is never targeted.
2. The trial collection defaults to `local_kb_kaiyuan_v2`; `local_kb_default` is not deleted or recreated.
3. Destructive recreation is an explicit target (`ingest-recreate`) rather than the default `make ingest` behavior.
4. `.env`, API keys, database/vector volumes, model files, caches, `.DS_Store` and machine-specific absolute paths are excluded.
5. Qdrant and PostgreSQL use named Docker volumes in the imported Compose baseline; no runtime database directory is committed.
6. Host Ollama remains supported through `host.docker.internal` for Apple Silicon.
7. The existing candidate inbox is excluded from ingest.

## Runtime Boundaries

B1 restores runnable infrastructure, but does not claim the final v2 retrieval contract or true incremental passage ingest. Those remain separate PRs:

- B2: passage identity, hash-based incremental insert/update/delete, `kb-text-core` ingestion;
- B3: explicit `query_mode`, `retrieval_stage`, `card_types`, `/v1/meta`, and real health contract;
- B4: candidate sync error states, citable evidence verification and golden integration tests.

## Verification

B1 is accepted when:

- runtime layout tests pass;
- Compose configuration contains required services and named data volumes;
- default collection is `local_kb_kaiyuan_v2`;
- default ingest is non-destructive;
- the API module imports with mocked external services;
- existing upstream candidate tests continue to pass;
- no forbidden local or secret files are committed;
- CI passes on Python 3.12.
