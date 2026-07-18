# Kaiyuan Stable Release and Rollback Drill Design

## Scope

B6-T03 adds a deterministic, non-mutating release drill for switching retrieval to `local_kb_kaiyuan_v2`, reconciling its corpus manifest, rolling routing back to the previously recorded collection, and proving that the protected legacy collection `local_kb_default` was unchanged. It does not ingest, switch a live service, mutate Qdrant, edit candidate manifests, or rewrite corpus files.

## Considered approaches

1. **Pure snapshot verifier (selected).** Operators capture three JSON observations—before switch, after switch, and after rollback—and a pure upstream verifier validates the complete transition. This is reproducible in CI, fail-closed, and cannot accidentally mutate production.
2. **Live Qdrant/API drill.** A script would query and reconfigure services directly. This better resembles production but requires credentials and introduces mutation and rollback risk inappropriate for repository CI.
3. **Runbook only.** Documentation has no executable proof that manifest reconciliation and protected-collection checks were performed.

## Architecture

`apps/local-kb-unified/release_drill.py` owns the release-drill contract and validation. It accepts an in-memory document with `before_switch`, `after_switch`, and `after_rollback` observations and returns a strict JSON-safe `kaiyuan-release-drill/v1` report. `apps/local-kb-unified/scripts/verify_release_drill.py` is a thin file-reading CLI that prints the report and exits nonzero unless `status=passed`.

Each observation records:

- `active_collection`;
- `health` with `status`, `ready`, and named boolean checks;
- `meta` with `meta_status` and the successful corpus manifest identity;
- `smoke` with a successful structured and primary retrieval result;
- `collections`, mapping collection names to immutable observed fingerprints.

A collection fingerprint contains `exists`, `points_count`, and `config_hash`. The protected collection's entire fingerprint must be identical in all three observations. The verifier never accepts credentials, Qdrant clients, mutation commands, source content, or raw response bodies.

## Transition semantics

The only release target is `local_kb_kaiyuan_v2`. Before switch, the recorded active collection may be another non-protected v2/ephemeral collection or `local_kb_default`; this is routing provenance, not authorization to write the legacy collection. After switch, the active collection, healthy default check, meta collection, and both smoke responses must all name `local_kb_kaiyuan_v2`.

Rollback must restore exactly the `before_switch.active_collection`. Its health, meta, and smoke observations must agree with that collection. If the previous active collection is `local_kb_default`, rollback may restore read routing to it, but the drill still requires an unchanged protected fingerprint and never writes, recreates, migrates, or ingests it.

Manifest reconciliation is identity-based. A successful observation requires `meta_status=ok`, `schema_version=corpus-manifest/v1`, non-empty `corpus_version`, `ingest_run_id`, `source_manifest_hash`, `collection`, `created_at`, `managed_by=local-kb-unified/v2`, and `collection_schema=passage-v2`. After switch, the supplied expected release manifest identity must match meta exactly. After rollback, meta must match the before-switch manifest identity exactly.

## Fail-closed validation

The verifier accumulates stable error codes but never converts invalid or missing observations into a healthy empty result. It rejects malformed roots, missing phases, wrong target, unready health, false required checks, collection/meta/smoke disagreement, empty smoke hits, manifest mismatch, missing protected snapshots, protected fingerprint drift, and rollback to anything other than the recorded prior collection.

The report contains `status=passed|failed`, `target_collection`, `rollback_collection`, `checks`, and `errors`. `checks` is an explicit boolean map; `errors` contains only stable code, phase, and field values safe for logs. No stack trace or secret-bearing response content is copied into the report. CLI input/JSON/contract failures are explicit stderr errors and exit code 2; a valid failed drill exits 1; a passed drill exits 0.

## Runbook and CI drill

`docs/development/B6_RELEASE_ROLLBACK_RUNBOOK.md` defines operator prerequisites, snapshot capture, manifest identity comparison, switch, smoke verification, rollback triggers, rollback verification, evidence recording, and the prohibition on deleting either collection during rollback.

CI runs the verifier against a committed synthetic fixture. The fixture uses only synthetic fingerprints and metadata; it does not contact Qdrant and does not claim a production release occurred. Production completion evidence must record the actual snapshot artifact hash, command result, release head, workflow runs, operator, and incident/rollback reason where applicable.

## Tests and compatibility

Unit tests first observe RED for the absent verifier, then cover a successful switch/rollback, rollback to a protected prior read target without protected drift, wrong target, unhealthy observations, manifest disagreement, empty retrieval, protected drift, and rollback provenance mismatch. Existing upstream and repository gates remain unchanged. The design is additive and does not alter ingest, search, evidence, candidate, corpus, Qdrant schema, or observability semantics.
