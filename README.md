# Chinese Star Omen Workspace

Monorepo for the Chinese star omen research system, including the official local knowledge-base runtime and the downstream research/query application.

## Release Branches

- `stable/kaiyuan-v2`: stable release base for the Kaiyuan v2 line.
- `dev-test`: integration/reference branch.
- `main`: historical workspace branch; Kaiyuan v2 releases are not merged into it.

Feature work targets short-lived `codex/*` branches and pull requests into `stable/kaiyuan-v2`.

## Apps

- `apps/local-kb-unified`: upstream official KB, Docker Compose, Qdrant ingest, KB Search API, and candidate approval/promotion. It is the source of truth.
- `apps/star-omen`: downstream query, `inspect-kb`, official two-stage retrieval, filesystem fallback, candidate generation, overlay and reconciliation. It does not write Qdrant.

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

## Retrieval Contract v2

The HTTP contract separates intent, stage and pool:

```text
query_mode      = evidence | knowledge | support
retrieval_stage = auto | structured_recall | primary_evidence | support_context
card_types      = explicit Qdrant card pool
```

The downstream app executes:

```text
Stage 1: official Qdrant structured recall
Stage 2: official Qdrant primary evidence
Fallback: local filesystem primary scan only when Stage 2 is empty
```

Official primary hits preserve volume/page/heading/paragraph offsets and hashes. Pending candidate overlays are returned only as `candidate_only` leads and never enter official primary or exact citable evidence.

Runtime endpoints:

```text
GET  /v1/health
GET  /v1/meta
POST /v1/retrieve
POST /v1/rag/query
```

See `apps/local-kb-unified/docs/agent-search-api.md` for complete request, response and error semantics.

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

Public-source and editorial-status records are stored in:

```text
corpus/kaiyuan_zhanjing/provenance.json
corpus/kaiyuan_zhanjing/baseline.json
```

The raw corpus remains immutable and unproofread; targeted source comparison reports differences instead of silently rewriting text.

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

Candidate generation remains usable offline and records upstream metadata as explicitly unavailable when `/v1/meta` cannot be reached. Pending candidates are never official evidence and never enter exact primary hits. Under the upstream `data/generated` tree, only approved/official cards enter the desired ingest corpus.

## Test Targets

```bash
make contracts-test
make text-core-test
make downstream-test
make upstream-test
```

CI runs:

- Python 3.9/3.12 text-core compatibility;
- contracts, upstream and downstream unit regressions;
- ephemeral Qdrant incremental reconciliation;
- ephemeral Qdrant retrieval-stage and missing-collection semantics;
- Docker Compose and forbidden-artifact gates.

## Invariants

1. Only upstream performs official ingest.
2. The downstream app remains read-only with respect to Qdrant.
3. Incoming and pending candidates are excluded from ingest.
4. Raw corpus text and `&KRxxxx;` entities are never guessed or rewritten.
5. Only `managed_by=local-kb-unified/v2` points are eligible for incremental stale deletion.
6. Filesystem fallback runs only after official primary Qdrant retrieval returns no primary evidence.
7. Secrets, model files and database/vector data are never committed.
8. Release work targets `stable/kaiyuan-v2`, not `main`.
