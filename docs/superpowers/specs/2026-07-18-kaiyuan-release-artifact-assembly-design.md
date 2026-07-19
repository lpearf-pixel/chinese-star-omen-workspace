# Kaiyuan Release Artifact Assembly Design

## Scope

B7-T02 adds an offline, fail-closed assembler for the three phase observations produced by B7-T01. It creates one `kaiyuan-release-drill-input/v1` document accepted by the existing B6 validator. It does not capture live state, change routing, execute rollback, connect to Qdrant, ingest, or mutate corpus/candidates/collections.

## Approaches considered

1. **Separate pure assembler plus CLI (selected).** Keeps input parsing, phase binding, manifest projection, B6 validation, and atomic output independently testable without changing verifier behavior.
2. **Extend `verify_release_drill.py`.** Fewer scripts, but mixes assembly mutation with a deliberately pure read-only verifier interface and complicates exit semantics.
3. **Document `jq`/shell assembly.** Minimal code, but preserves duplicate-key, wrong-schema, wrong-slot, manifest-copy, portability, and partial-write risks.

## Inputs and output

The CLI requires four explicit existing UTF-8 JSON files: `--before-switch`, `--after-switch`, `--after-rollback`, and `--expected-manifest`, plus caller-selected `--out`. There is no default output path and overwrite is forbidden.

Each observation must be a strict JSON object with `schema_version=kaiyuan-release-observation/v1`, the exact expected `phase_name`, a canonical UTC RFC3339 `captured_at`, and a mapping-valued `phase`. The three timestamps must be strictly increasing in release sequence. Extra top-level observation fields are rejected so unreviewed data cannot be copied into the final artifact.

The expected manifest may be a full corpus manifest, but the assembler projects only `MANIFEST_IDENTITY_FIELDS`. All identity values must be non-empty strings and must satisfy the B6 manifest schema, manager, collection schema, and target collection requirements. No other manifest field enters the artifact.

The output contains exactly `schema_version`, `target_collection`, `expected_release_manifest`, `before_switch`, `after_switch`, and `after_rollback`. Phase payloads are copied only after their observation envelopes pass validation.

## Data flow

1. Strictly parse all four inputs with duplicate-key and non-finite token rejection.
2. Validate observation envelopes, exact slot binding, canonical UTC timestamps, and strict chronology.
3. Project and validate the approved release manifest identity for `local_kb_kaiyuan_v2`.
4. Construct the B6 input document in memory and call `validate_release_drill`.
5. If the report status is not `passed`, return a stable validation failure and print only the existing safe report; do not create output.
6. If passed, serialize strict finite JSON and atomically create the caller-selected output without overwrite or temporary residue.

## Error semantics

Invocation, file, UTF-8, duplicate-key, JSON, envelope, timestamp, manifest, and output-contract failures exit `2` with a stable assembler input code. A well-formed assembled document rejected by B6 exits `1` and emits the content-free B6 report. Success exits `0` and emits only phase names, output path, and artifact SHA-256; it never copies source JSON or manifest content to stdout/stderr.

No exception becomes a partial artifact or healthy result. A concurrent output creator is classified as `output_exists`. Temporary files are same-directory, fsynced, exclusively linked, and removed on every path.

## Compatibility and safety

The existing B6 validator and verifier CLI remain unchanged. The assembler imports their constants and validator rather than duplicating phase semantics. It has no HTTP/Qdrant/ingest imports. Tests use only committed synthetic fixtures and temporary paths; `local_kb_default` may appear as immutable fingerprint data but is never accessed or written.

## Tests

TDD covers happy-path assembly accepted by B6, exact output shape, wrong/missing/duplicate phase names, swapped files, invalid observation schema, non-object phase, timestamp format/order, duplicate/non-finite JSON, invalid or wrong-collection manifest identity, B6 validation failure with no output, strict atomic creation/no-overwrite/race cleanup, safe stderr/report output, and production-source mutation/import scans.
