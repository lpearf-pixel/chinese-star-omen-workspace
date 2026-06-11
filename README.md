# Chinese Star Omen Workspace

Monorepo workspace for the Chinese star omen research system.

## Apps

- `apps/local-kb-unified`: upstream official KB, ingest, Qdrant, KB Search API, and candidate approval/promotion. It is the source of truth.
- `apps/star-omen`: downstream query, `inspect-kb`, filesystem fallback, candidate card generation, runtime overlay, and sync reconciliation. It must not run upstream ingest or write Qdrant.

## Shared Packages

- `packages/kb-contracts`: the single shared source for candidate/corpus schemas, status enums, normalization, hashes, stable ids, and manifest helpers.

When running scripts directly, expose the shared Python helpers with:

```bash
export PYTHONPATH="$PWD/packages/kb-contracts/python:$PYTHONPATH"
```

## Open-source Kaiyuan source sync

The downstream filesystem fallback and candidate generator can use the public `lpearf-pixel/kaiyuanzhanjin` text layout directly. To copy that repo into both upstream and downstream source roots, run:

```bash
make sync-kaiyuan-source
```

If the repo is already cloned locally, avoid network access and use:

```bash
python scripts/sync_kaiyuan_source.py \
  --source-dir /path/to/kaiyuanzhanjin \
  --clean
```

The sync script writes the source under `data/sources/古籍/唐開元占經/`, preserving folders such as `分卷/` and `唐開元占經-全文合併版.md`, so existing path inference resolves `book_id=kaiyuan_zhanjing` and primary `fenjuan/fulltext` card types.

## Candidate Sync v1 Flow

```bash
make generate-candidate
# copy candidate files to apps/local-kb-unified/incoming/downstream_candidates/codex-ready
make validate-candidates
# manually approve by changing review_status=approved
make promote-candidates
make ingest
make sync
```

Detailed upstream procedure: `apps/local-kb-unified/docs/downstream-candidate-sync-v1.md`.

## Common Commands

```bash
make up
make ingest
make health
make sync-kaiyuan-source
make inspect-kaiyuan
make generate-candidate
make validate-candidates
make promote-candidates
make sync
make contracts-test
make downstream-test
make upstream-test
```

## Invariants

1. `apps/local-kb-unified` is the source of truth.
2. Only upstream performs official `make ingest` into the official Qdrant collection.
3. Downstream generates candidates only under `apps/star-omen/data/generated_candidates/`.
4. Pending candidates are never official evidence and never enter `exact_hits`.
5. Runtime candidate overlay is disabled by default (`KB_ENABLE_CANDIDATE_OVERLAY=false`).
