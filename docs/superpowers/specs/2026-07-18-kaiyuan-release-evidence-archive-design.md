# Kaiyuan Release Evidence Archive Index Design

## Scope

B8-T01 verifies multiple sealed B7-T03 bundles and creates a deterministic archive index with retention classifications. It never moves, overwrites, truncates, or deletes a bundle. It does not connect to GitHub, KB Search, Qdrant, or any other service and does not authorize release, rollback, ingest, or collection changes.

## Approaches considered

1. **Explicit bundle map plus content-free JSON index (selected).** The caller supplies repeated `logical-name=path` bindings. Paths are used only to read locally and never enter the index. Every bundle is fully verified before an in-memory index is atomically created.
2. **Scan a directory automatically.** Convenient, but silently changes scope when unrelated ZIP files appear and makes invalid files ambiguous. Explicit inputs are safer and reproducible.
3. **Move/delete bundles according to retention policy.** Operationally direct, but irreversible and outside evidence verification. Classification only preserves human control and auditability.

## Inputs and index schema

The create CLI requires one or more repeated `--bundle <logical-name>=<path>` arguments, `--keep-latest <positive integer>`, zero or more `--pin <sha256:...>` arguments, and caller-selected `--out`. Logical names must be unique ASCII slugs matching `[A-Za-z0-9][A-Za-z0-9._-]{0,127}` and contain no slash. Bundle paths and parent directories are never serialized.

Each input is read with an exact byte limit and passed to `verify_bundle_bytes`. The creator also strictly reads the internal bundle manifest through the existing B7-T03 parser so it can project only bundle SHA-256, logical name, release head, created time, target collection, schema, and tool identity. Duplicate bundle hashes fail rather than aliasing one file under multiple names.

The output schema is `kaiyuan-release-evidence-archive/v1` and contains exactly:

- `schema_version`
- `policy` with `keep_latest` and sorted unique `pinned_bundle_hashes`
- `entries`

Each entry contains exactly `logical_name`, `bundle_sha256`, `bundle_schema`, `release_head`, `created_at`, `target_collection`, `classification`, and `reasons`. It contains no source path, filesystem metadata, raw observation, manifest content, hit, snippet, anchor, secret, or error body.

## Retention classification

Entries are grouped by target collection and sorted by canonical `created_at` descending, then release head ascending, then bundle hash ascending. The first `keep_latest` entries in each group are `retain` with reason `latest`. Any hash listed in `pinned_bundle_hashes` is also `retain` with reason `pinned`; reasons use fixed order `pinned`, then `latest`. Every remaining entry is `cold_archive_eligible` with reason `outside_keep_latest`.

Every pin must match exactly one supplied bundle. Unknown, duplicate, non-lowercase, or malformed pins fail closed. `keep_latest` rejects bool, zero, negative, string, and values above 10,000. Classification does not imply deletion and no production code contains a delete or move operation.

Final index entries use ascending `(target_collection, created_at, release_head, bundle_sha256)` order independent of input order. Reordered inputs therefore produce identical index bytes.

## Verification and atomicity

A separate offline verifier accepts an index plus the same explicit logical-name/path bundle map. It strictly parses the index, checks exact keys/types/order/policy/classification, requires the supplied logical-name set to match exactly, re-verifies every B7-T03 bundle, rebuilds the index in memory, and requires exact semantic and canonical-byte equality. It emits only schema, counts, classifications, and index SHA-256.

The creator serializes sorted finite canonical JSON with one trailing newline, writes a same-directory temporary file, fsyncs it, and hard-links it to the caller-selected output. Pre-existing or concurrently created output fails with `output_exists`; temporary residue is removed on every path.

## Error semantics and safety

Invocation/read/index-contract/output errors exit `2`; invalid or tampered bundles and index mismatches exit `1`. Stable content-free codes distinguish invalid arguments, duplicate name/hash, unknown pin, bundle verification failure, index mismatch, output exists, and write failure. No traceback, local path, input content, or bundle member is printed.

Tests use only synthetic content-free B7 bundles in temporary directories. The implementation imports no HTTP, Qdrant, ingest, routing, corpus, candidate, delete, rename, or move functionality. `local_kb_default` may occur inside already sealed fingerprint evidence but is never accessed or mutated.

## Tests

TDD covers deterministic creation independent of input order, exact index shape, keep-latest and pin overlap reasons, per-target sorting, malformed/unknown/duplicate pins, invalid keep counts, unsafe/duplicate logical names, duplicate bundle hash, invalid/tampered/trailing-byte bundle, strict canonical index JSON, missing/extra/mismatched verifier bundle map, policy/classification/order tampering, atomic no-overwrite/race cleanup, safe CLI diagnostics, and forbidden production imports/mutation calls.
