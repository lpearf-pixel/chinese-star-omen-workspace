# Kaiyuan Release Observation Capture Design

## Scope

B7-T01 adds a local, read-only collector that creates one B6 release-drill phase observation from live KB Search and Qdrant read APIs. It does not assemble a three-phase verdict, change routing, restart services, ingest, mutate any collection, or write a default output path.

## Approaches considered

1. **Local direct-read CLI (selected).** Read health/meta/retrieve through KB Search and collection metadata through Qdrant. This automates provenance without expanding the server API.
2. **New KB Search inspection endpoint.** Easier for remote operators, but unnecessarily exposes protected collection metadata and enlarges the authenticated service surface.
3. **Operator-supplied collection fingerprint.** Lowest implementation cost, but preserves the manual error and fabrication risk B7 is intended to remove.

## Components

`apps/local-kb-unified/release_observation.py` is a pure orchestration and validation module with injected `fetch_health`, `fetch_meta`, `retrieve`, and `inspect_collection` callables. It returns `kaiyuan-release-observation/v1` only after every call succeeds and every response satisfies the B6 phase contract.

`apps/local-kb-unified/scripts/capture_release_observation.py` provides the live adapters. It requires an explicit phase name, active collection, query, KB Search base URL, Qdrant URL, API key environment-variable name, and caller-selected output path. It atomically creates a new file and refuses overwrite.

## Data flow

1. GET `/v1/health`; require HTTP 200, `status=ok`, `ready=true`, all B6 checks true, and `default_collection=active_collection`.
2. GET `/v1/meta`; require HTTP 200, `meta_status=ok`, complete typed manifest identity, and `collection=active_collection`.
3. POST `/v1/retrieve` twice with an explicit collection, `kb_book_id=kaiyuan_zhanjing`, and exact B6 stage pools. Require HTTP 200, exact effective stage/pool/collection, and a positive `retrieved_count` consistent with the hit-list length. The artifact stores counts and provenance only, never hits, snippets, paths, anchors, or source content.
4. Read `get_collection` and exact `count` for the active and protected collections. Require both exist. Build a deterministic SHA-256 config fingerprint from an allowlist of vector size/distance, shard/replication/write-consistency, on-disk payload, and optimizer/index settings after strict JSON normalization.
5. Return the observation plus capture metadata containing phase and a UTC timestamp. The B6 phase payload remains directly consumable when assembling the three-phase document.

## Error and secret boundary

Errors use a dedicated `ReleaseObservationError` with stable codes: `authentication_failed`, `upstream_unavailable`, `timeout`, `contract_error`, `collection_not_found`, `invalid_response`, and `output_exists`. No exception is converted to zero hits or an incomplete observation.

The API key is read from the named environment variable, sent only as an authorization header, and never included in arguments echoed to output, artifacts, or structured error details. Raw HTTP bodies, Qdrant exception messages, collection payload samples, hits, and source text are never persisted. CLI stderr contains only stable code and operation.

## Collection safety

The live module imports no ingest code and calls only GET/retrieve and Qdrant `get_collection`, `collection_exists`, and `count`. Tests use fakes and random ephemeral names; no test connects to or writes `local_kb_default`. The protected collection is observed, not modified.

## Determinism and compatibility

Config fingerprints sort keys, reject non-finite values, normalize enums to their public string values, and hash UTF-8 canonical JSON. The collector is additive and does not change B6 verifier, KB Search endpoints, retrieval semantics, corpus, candidates, or Qdrant schema.

## Tests

TDD covers a valid capture, exact request pools, redacted output, authentication/timeout/5xx/invalid JSON, contract mismatches, healthy zero hits, missing collections, deterministic config hashing, prohibited non-finite metadata, and atomic no-overwrite output. A committed synthetic adapter test proves the captured phase can replace a fixture phase accepted by the B6 verifier.
