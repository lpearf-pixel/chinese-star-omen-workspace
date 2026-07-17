# Chinese Star Omen Workspace

Monorepo for the Chinese star omen research system, including the official local knowledge-base runtime and the downstream research/query application.

## Release Branches

- `stable/kaiyuan-v2`: stable release base for the Kaiyuan v2 line.
- `dev-test`: integration/reference branch.
- `main`: historical workspace branch; Kaiyuan v2 releases are not merged into it.

Feature work targets short-lived `codex/*` branches and pull requests into `stable/kaiyuan-v2`.

## Apps

- `apps/local-kb-unified`: upstream official KB, Docker Compose, Qdrant ingest, KB Search API, and candidate approval/promotion. It is the source of truth.
- `apps/star-omen`: downstream query, `inspect-kb`, filesystem fallback, candidate generation, overlay and reconciliation. It does not write Qdrant.

## Shared Packages

- `packages/kb-contracts`: candidate/corpus schemas, states, hashes, stable IDs and manifest helpers.
- `packages/kb-text-core`: immutable Kaiyuan parsing, conservative normalization, raw-offset matching, page/heading anchors, passage identity, ranking and primary-evidence deduplication.

## Upstream Runtime

The real Local-KB-Unified runtime is restored under `apps/local-kb-unified`. It runs Qdrant, PostgreSQL, KB Search and OpenWebUI through Docker Compose while using host Ollama on macOS/Apple Silicon.

The v2 trial collection is:

```text
local_kb_kaiyuan_v2
```

The existing `local_kb_default` collection is not recreated or deleted by default.

```bash
cd apps/local-kb-unified
cp .env.example .env
# replace placeholder secrets in .env
make setup
make pull-models
make up
make health
make ingest-dry-run
make ingest
```

`make ingest` performs passage-level incremental reconciliation:

```text
unchanged → no embedding
new/changed → embed + upsert
stale v2-managed → delete only after all required upserts succeed
```

Additional modes:

```bash
make ingest-full
make ingest-recreate
```

Destructive recreation is explicit. Runtime source provenance is recorded in `apps/local-kb-unified/RUNTIME_BASELINE.json`.

## Kaiyuan Corpus Audit and Retrieval

The combined fulltext is an immutable audit baseline. `KR3g0018_000.md` through `KR3g0018_120.md` are derived retrieval views.

```bash
make sync-kaiyuan-source
make audit-kaiyuan-corpus
make audit-kaiyuan-baseline
make compare-kaiyuan-volumes
make inspect-kaiyuan
```

The same `kb-text-core` page/heading/offset semantics are used by official Qdrant ingest and filesystem fallback. `fenjuan` evidence is retained ahead of duplicate `fulltext` evidence while duplicate provenance remains traceable.

## Candidate Workflow

```bash
make generate-candidate
# submit reviewed artifacts to the upstream inbox
make validate-candidates
# manually set approved candidates to review_status=approved
make promote-candidates
make ingest
make sync
```

Pending candidates are never official evidence and never enter exact primary hits. Under the upstream `data/generated` tree, only approved/official cards enter the desired ingest corpus.

## Test Targets

```bash
make contracts-test
make text-core-test
make downstream-test
make upstream-test
```

CI also runs an ephemeral Qdrant reconciliation test for insert, unchanged skip, changed update and stale deletion.

## Invariants

1. Only upstream performs official ingest.
2. The downstream app remains read-only with respect to Qdrant.
3. Incoming and pending candidates are excluded from ingest.
4. Raw corpus text and `&KRxxxx;` entities are never guessed or rewritten.
5. Only `managed_by=local-kb-unified/v2` points are eligible for incremental stale deletion.
6. Secrets, model files and database/vector data are never committed.
7. Release work targets `stable/kaiyuan-v2`, not `main`.
