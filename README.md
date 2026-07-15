# Chinese Star Omen Workspace

Monorepo workspace for the Chinese star omen research system.

## Apps

- `apps/local-kb-unified`: upstream official KB, ingest, Qdrant, KB Search API, and candidate approval/promotion. It is the source of truth.
- `apps/star-omen`: downstream query, `inspect-kb`, filesystem fallback, candidate card generation, runtime overlay, and sync reconciliation. It must not run upstream ingest or write Qdrant.

## Shared Packages

- `packages/kb-contracts`: the single shared source for candidate/corpus schemas, status enums, hashes, stable ids, and manifest helpers.
- `packages/kb-text-core`: the shared read-only Kaiyuan parser, query normalization, raw-offset matching, page/heading anchors, ranking, and primary-evidence deduplication used by fallback retrieval and candidate generation.

When running scripts directly, expose both shared Python packages with:

```bash
export PYTHONPATH="$PWD/packages/kb-contracts/python:$PWD/packages/kb-text-core/python:$PYTHONPATH"
```

## Open-source Kaiyuan source sync

The downstream filesystem fallback and candidate generator can use the public `lpearf-pixel/kaiyuanzhanjin` text layout directly. To copy that repo into both upstream and downstream source roots, run:

```bash
make sync-kaiyuan-source
```

If the repo is already cloned locally, avoid network access and use:

```bash
KAIYUAN_SOURCE_DIR=/path/to/kaiyuanzhanjin make sync-kaiyuan-source
# or:
python scripts/sync_kaiyuan_source.py \
  --source-dir /path/to/kaiyuanzhanjin \
  --clean
```

The sync script writes the source under `data/sources/古籍/唐開元占經/`, preserving folders such as `分卷/` and `唐開元占經-全文合併版.md`, so path inference resolves `kb_book_id=kaiyuan_zhanjing` and primary `fenjuan/fulltext` card types.

## Kaiyuan corpus audit and retrieval v2

The combined fulltext is treated as an immutable audit baseline and the 121 files `KR3g0018_000.md` through `KR3g0018_120.md` are derived retrieval views. The audit does not overwrite either source.

```bash
make audit-kaiyuan-corpus
make text-core-test
make inspect-kaiyuan
```

The v2 fallback scans the complete candidate pool before applying the limit, preserves original character offsets, returns the actual matching excerpt, extracts `<pb:...>` page markers and headings, and prefers `fenjuan` over duplicate `fulltext` evidence. Details: `docs/kaiyuan-corpus-retrieval-v2.md`.

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
make audit-kaiyuan-corpus
make inspect-kaiyuan
make generate-candidate
make validate-candidates
make promote-candidates
make sync
make contracts-test
make text-core-test
make downstream-test
make upstream-test
```

## Invariants

1. `apps/local-kb-unified` is the source of truth.
2. Only upstream performs official `make ingest` into the official Qdrant collection.
3. Downstream generates candidates only under `apps/star-omen/data/generated_candidates/`.
4. Pending candidates are never official evidence and never enter `exact_hits`.
5. Runtime candidate overlay is disabled by default (`KB_ENABLE_CANDIDATE_OVERLAY=false`).
6. Search normalization never rewrites the immutable raw corpus; `&KRxxxx;` entities remain unchanged until an authoritative mapping is supplied.
