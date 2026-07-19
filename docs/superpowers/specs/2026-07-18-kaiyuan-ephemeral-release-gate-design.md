# Kaiyuan Hermetic End-to-End Release Evidence Gate Design

## Scope

B8-T02 adds a hermetic CI gate that composes the existing B7 release-observation, artifact-assembly, sealed-bundle, and offline-verification contracts. It detects cross-component drift without network credentials, routing changes, ingest, corpus access, or Qdrant mutation. Its output is synthetic CI evidence, never production-release evidence.

## Approaches considered

1. **One hermetic pytest using real pure APIs and audited read-only adapters (selected).** This exercises the semantic boundaries end to end, remains deterministic, and makes forbidden collection access observable without adding production orchestration.
2. **A production orchestration CLI.** This would duplicate operator timing and routing responsibilities, expand the mutation boundary, and require secrets.
3. **Docker Compose with live KB Search and Qdrant.** This gives transport coverage but cannot safely perform three routing phases in ordinary PR CI. Existing tests cover live adapters and ephemeral Qdrant contracts separately.

## Gate data flow

The test creates a random identifier matching `ephemeral_kaiyuan_release_<hex>` for the safe pre-release active collection. Deterministic fake KB Search and collection-inspection adapters expose only the read methods accepted by `capture_phase_observation`. Each adapter records a structured operation before returning a content-free response.

The gate captures `before_switch`, `after_switch`, and `after_rollback` at fixed canonical UTC instants. Before and after rollback use the ephemeral active collection and its manifest identity; after switch uses `local_kb_kaiyuan_v2` and the approved release manifest identity. The protected legacy fingerprint required by the B6 input contract is synthetic invariant evidence returned only by the hermetic fake inspector; no live client or service is instantiated.

The observations and approved manifest pass to `assemble_release_artifact`; its report must be exactly passed. The assembled document passes to `create_bundle_bytes` with fixed explicit provenance, and the bytes pass to `verify_bundle_bytes`. The verifier summary must exactly identify the release head, target collection, schema, and member count.

## Safety and fail-closed rules

The call audit allowlists health, meta, the two retrieval stages, and read-only inspection. `local_kb_default` must appear exactly once per phase as a fake inspection needed by the existing invariant contract, never as a network or mutation call. The audit rejects mutation-like operations. The gate never imports index jobs, candidate promotion, routing, live clients, or mutation clients.

An explicit failure case corrupts one phase after capture. Assembly must raise its stable validation error, no bundle may be produced, and offline verification is not invoked. Exceptions are not converted into empty results or a passed report.

## CI integration and compatibility

The focused test lives in `apps/local-kb-unified/tests/test_release_evidence_e2e_v1.py` and is invoked as a named step in `kaiyuan-upstream-runtime.yml`. Existing production modules and CLIs remain unchanged. The gate uses no secret, service container, filesystem corpus, candidate manifest, Qdrant collection, or `local_kb_default` access.

## Tests

TDD covers successful capture-to-verification composition, exact deterministic summaries, fixed phase ordering, random safe ephemeral naming, operation audit, protected fingerprint inspection confined to the fake, absence of mutation operations, and fail-closed phase tampering before bundle creation.
