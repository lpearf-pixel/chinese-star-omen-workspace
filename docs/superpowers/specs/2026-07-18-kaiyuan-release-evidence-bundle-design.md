# Kaiyuan Release Evidence Bundle Design

## Scope

B7-T03 seals the content-free B7 release observations, approved manifest identity, assembled B6 drill input, and validation report into one deterministic evidence file. A separate offline verifier authenticates the internal bytes and reruns the assembly and B6 validation contracts. The feature does not capture live state, connect to a service, extract source content, change routing, ingest, or mutate Qdrant, corpus, candidates, or collections.

## Approaches considered

1. **Deterministic ZIP with an internal strict inventory (selected).** A single file can be atomically published without overwrite using the repository's temporary-file plus hard-link pattern. The verifier reads members without extracting them, rejects duplicate or unexpected names, checks exact bytes, then reruns semantic validation.
2. **Atomic directory tree.** Human-readable in place, but POSIX rename can replace a concurrently created empty directory, while creating the final directory first exposes a partial bundle. It cannot meet both atomic publication and strict no-overwrite without platform-specific system calls.
3. **Manifest containing external file references.** Smallest implementation, but paths break when evidence is moved and referenced files can change independently. It is not a sealed release record.

## Inputs and bundle members

The bundle CLI requires the same three strict observation files and approved manifest used by B7-T02, the assembled release-drill input, an explicit 40-character lowercase Git release head, an explicit canonical UTC `created_at`, and a caller-selected output path. There are no defaults for provenance or output.

The creator strictly parses every JSON input, reruns `assemble_release_artifact`, requires the supplied assembled input to equal the newly assembled document, and requires B6 validation to pass. It then writes exactly these canonical UTF-8 JSON members:

- `before-switch.json`
- `after-switch.json`
- `after-rollback.json`
- `expected-manifest-identity.json`
- `release-drill-input.json`
- `validation-report.json`
- `bundle-manifest.json`

The first six members are listed in `bundle-manifest.json` with exact member name, schema role, byte size, and `sha256:<64 lowercase hex>` digest. The bundle manifest additionally records `schema_version=kaiyuan-release-evidence-bundle/v1`, `release_head`, canonical UTC `created_at`, target collection, tool identity/version, and exact ordered inventory. It does not hash itself and contains no filesystem path.

Only the allowlisted manifest identity enters the bundle. Observation and drill payloads have already passed the content-free B7/T02 contracts; unknown fields are rejected before serialization. The validator report is generated internally and cannot be supplied by the caller.

## Deterministic archive and atomic publication

The ZIP uses stored, unencrypted members in one fixed order. Every `ZipInfo` uses a fixed timestamp, regular-file mode, creator system, and empty comment/extra fields. JSON serialization uses sorted keys, UTF-8, finite numbers, and one trailing newline. These rules make identical logical inputs byte-identical.

The complete archive is written and fsynced as a same-directory temporary file, then hard-linked to the final caller-selected path. A pre-existing or concurrently created output fails with `output_exists`; the final file is never overwritten. Every error removes temporary residue.

## Offline verification

The verifier accepts one bundle path and performs no extraction. It fails closed unless the archive has the exact seven unique regular-file members, no encryption, no compression, no comments/extra data, fixed metadata, bounded member/archive sizes, and no traversal-like names. It strictly parses the bundle manifest, requires exact ordered inventory, verifies every listed byte size and digest, and validates all provenance formats.

After byte verification it strictly parses the six evidence members, reruns B7-T02 assembly from the observations and manifest identity, requires exact semantic equality with `release-drill-input.json`, reruns B6 validation, and requires exact equality with `validation-report.json`. Success prints only schema, release head, target collection, member count, and bundle SHA-256. Failure prints a stable content-free code and exits nonzero; no input value or member content is copied to stderr.

## Error semantics

Creator invocation/input/provenance/output errors exit `2`; semantic drill failure exits `1`. Verifier malformed archive, manifest, hash, inventory, or semantic mismatch exits `1`; unreadable input or invalid invocation exits `2`. Stable codes distinguish invalid JSON, invalid provenance, archive contract failure, inventory mismatch, member hash/size mismatch, assembly mismatch, and drill validation failure. No exception becomes a healthy result or partial artifact.

## Compatibility and safety

B6 validation, B7 observation capture, and B7-T02 assembly interfaces remain unchanged. New modules import and reuse their constants and pure functions. Production code has no HTTP, Qdrant, ingest, routing, or corpus imports. `local_kb_default` may occur only inside the already allowlisted immutable fingerprint evidence and is never accessed or modified.

## Tests

TDD covers deterministic happy-path creation/verification, exact member inventory and metadata, release-head/timestamp validation, supplied-artifact mismatch, internally generated report, duplicate/non-finite JSON, ZIP duplicate/unexpected/traversal/encrypted/compressed/oversized members, manifest extra/missing/reordered entries, byte size/hash tampering, semantic observation/artifact/report mismatch even with recomputed hashes, atomic no-overwrite/race cleanup, safe diagnostics, and forbidden production imports or mutation calls.
