from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable, Mapping

from src.connectors.evidence_resolver import EvidenceResolverContext, resolve_evidence
from src.video_pipeline.contracts.external_media_v1 import ExternalAuditBundleV1
from src.video_pipeline.feedback_loop.contracts_v1 import LocalEvidenceProbeV1
from src.video_pipeline.feedback_loop.readonly_adapter_v1 import (
    REJECTION_STATUSES,
    ProjectionResultV1,
    ValidatedTwoStageResultV1,
    project_citable_references,
    validate_two_stage_response,
)
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalEvidenceProbeRequestV1,
    LocalEvidenceQueryPlanV1,
    LocalKBSourceSnapshotV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
    ReadOnlyTwoStageRetriever,
    SourceSnapshotBindingV1,
    canonical_contract_sha256,
)
from src.video_pipeline.feedback_loop.source_snapshot_v1 import LocalKBSourceAccessor


_POLICY_VERSION = "vfl-readonly-probe/1.0.0"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _safe_failure(
    code: ReadOnlyErrorCode,
    *,
    failed_claim_id: str | None = None,
) -> None:
    raise ReadOnlyAdapterError(code, failed_claim_id=failed_claim_id) from None


def _audit_matches_plan(
    *,
    audit_bundle: ExternalAuditBundleV1,
    query_plan: LocalEvidenceQueryPlanV1,
) -> bool:
    audit_claim_ids = tuple(sorted(claim.claim_id for claim in audit_bundle.claims))
    request_claim_ids = tuple(request.claim_id for request in query_plan.requests)
    return (
        query_plan.source_id == audit_bundle.source.source_id
        and query_plan.audit_id == audit_bundle.audit.audit_id
        and request_claim_ids == audit_claim_ids
    )


def _preflight(
    *,
    audit_bundle: ExternalAuditBundleV1,
    query_plan: LocalEvidenceQueryPlanV1,
    plan_sha256: str,
    retriever: ReadOnlyTwoStageRetriever,
    kb_root: Path,
    source_snapshot: LocalKBSourceSnapshotV1,
    source_snapshot_sha256: str,
    source_accessor: LocalKBSourceAccessor,
) -> None:
    failure_code: ReadOnlyErrorCode | None = None
    try:
        if (
            canonical_contract_sha256(query_plan) != plan_sha256
            or not _audit_matches_plan(
                audit_bundle=audit_bundle,
                query_plan=query_plan,
            )
        ):
            raise ReadOnlyAdapterError(ReadOnlyErrorCode.PLAN_MISMATCH)
        if (
            canonical_contract_sha256(source_snapshot) != source_snapshot_sha256
            or source_snapshot.collection != query_plan.collection
            or source_snapshot.kb_book_id != query_plan.kb_book_id
            or source_snapshot.corpus_version
            != query_plan.expected_corpus_version
        ):
            raise ReadOnlyAdapterError(ReadOnlyErrorCode.SNAPSHOT_MISMATCH)
        source_binding = retriever.source_binding
        if (
            type(source_binding) is not SourceSnapshotBindingV1
            or source_binding != source_accessor.binding
        ):
            raise ReadOnlyAdapterError(ReadOnlyErrorCode.SNAPSHOT_MISMATCH)
        source_accessor.assert_bound(
            kb_root=kb_root,
            snapshot=source_snapshot,
            snapshot_sha256=source_snapshot_sha256,
        )
        source_accessor.assert_unchanged()
    except ReadOnlyAdapterError as exc:
        failure_code = exc.code
    except Exception:
        failure_code = ReadOnlyErrorCode.SNAPSHOT_MISMATCH
    if failure_code is not None:
        _safe_failure(failure_code)


def _retrieval_version(
    *,
    plan_sha256: str,
    source_snapshot_sha256: str,
    validated: ValidatedTwoStageResultV1,
) -> str:
    payload = {
        "policy_version": _POLICY_VERSION,
        "plan_sha256": plan_sha256,
        "upstream_provenance_sha256": validated.upstream_provenance_sha256,
        "corpus_provenance": validated.corpus_provenance,
        "source_snapshot_sha256": source_snapshot_sha256,
        "response_schema_versions": list(validated.response_schema_versions),
    }
    return (
        f"{_POLICY_VERSION}:sha256:"
        f"{hashlib.sha256(_canonical_bytes(payload)).hexdigest()}"
    )


def _reference_payloads(projection: ProjectionResultV1) -> list[dict[str, object]]:
    payloads = [
        reference.model_dump(mode="json") for reference in projection.references
    ]
    return sorted(payloads, key=_canonical_bytes)


def _probe_id(
    *,
    query_plan: LocalEvidenceQueryPlanV1,
    request: LocalEvidenceProbeRequestV1,
    plan_sha256: str,
    source_snapshot_sha256: str,
    validated: ValidatedTwoStageResultV1,
    projection: ProjectionResultV1,
) -> str:
    payload = {
        "policy_version": query_plan.policy_version,
        "plan_sha256": plan_sha256,
        "plan_id": query_plan.plan_id,
        "execution_scope": query_plan.execution_scope,
        "request_id": request.request_id,
        "source_id": request.source_id,
        "claim_id": request.claim_id,
        "query": request.query,
        "top_k": request.top_k,
        "collection": query_plan.collection,
        "expected_corpus_version": query_plan.expected_corpus_version,
        "observed_corpus_version": validated.observed_corpus_version,
        "upstream_provenance_sha256": validated.upstream_provenance_sha256,
        "corpus_provenance": validated.corpus_provenance,
        "source_snapshot_sha256": source_snapshot_sha256,
        "response_schema_versions": list(validated.response_schema_versions),
        "evidence_references": _reference_payloads(projection),
    }
    return f"probe:vfl:s1:{hashlib.sha256(_canonical_bytes(payload)).hexdigest()}"


def _notes(
    *,
    query_plan: LocalEvidenceQueryPlanV1,
    request: LocalEvidenceProbeRequestV1,
    source_snapshot_sha256: str,
    validated: ValidatedTwoStageResultV1,
    projection: ProjectionResultV1,
) -> list[str]:
    rejection_counts = dict(projection.rejection_counts)
    return [
        f"plan_id={query_plan.plan_id}",
        f"request_id={request.request_id}",
        f"collection={query_plan.collection}",
        f"expected_corpus_version={query_plan.expected_corpus_version}",
        f"observed_corpus_version={validated.observed_corpus_version}",
        "upstream_provenance_sha256="
        f"{validated.upstream_provenance_sha256}",
        f"corpus_provenance={validated.corpus_provenance}",
        f"top_k={request.top_k}",
        f"exact_candidate_count={validated.exact_candidate_count}",
        f"citable_count={len(projection.references)}",
        f"source_snapshot_sha256={source_snapshot_sha256}",
        *[
            f"rejected.{status}={rejection_counts[status]}"
            for status in REJECTION_STATUSES
        ],
    ]


def _build_probe(
    *,
    query_plan: LocalEvidenceQueryPlanV1,
    request: LocalEvidenceProbeRequestV1,
    plan_sha256: str,
    source_snapshot_sha256: str,
    validated: ValidatedTwoStageResultV1,
    projection: ProjectionResultV1,
) -> LocalEvidenceProbeV1:
    return LocalEvidenceProbeV1(
        schema_version="local-evidence-probe/v1",
        probe_id=_probe_id(
            query_plan=query_plan,
            request=request,
            plan_sha256=plan_sha256,
            source_snapshot_sha256=source_snapshot_sha256,
            validated=validated,
            projection=projection,
        ),
        source_id=request.source_id,
        claim_id=request.claim_id,
        query=request.query,
        corpus_version=validated.observed_corpus_version,
        retrieval_version=_retrieval_version(
            plan_sha256=plan_sha256,
            source_snapshot_sha256=source_snapshot_sha256,
            validated=validated,
        ),
        result_state="unresolved",
        evidence_references=list(projection.references),
        notes=_notes(
            query_plan=query_plan,
            request=request,
            source_snapshot_sha256=source_snapshot_sha256,
            validated=validated,
            projection=projection,
        ),
    )


def _retrieve(
    *,
    retriever: ReadOnlyTwoStageRetriever,
    request: LocalEvidenceProbeRequestV1,
    query_plan: LocalEvidenceQueryPlanV1,
) -> Mapping[str, object]:
    result: Mapping[str, object] | None = None
    failure_code: ReadOnlyErrorCode | None = None
    try:
        result = retriever.two_stage_retrieve(
            request.query,
            top_k=request.top_k,
            collection=query_plan.collection,
            filters={"kb_book_id": request.kb_book_id},
            query_mode="evidence",
        )
    except ReadOnlyAdapterError as exc:
        failure_code = exc.code
    except Exception:
        failure_code = ReadOnlyErrorCode.TRANSPORT_FAILED
    if failure_code is not None:
        _safe_failure(failure_code, failed_claim_id=request.claim_id)
    if not isinstance(result, Mapping):
        _safe_failure(
            ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED,
            failed_claim_id=request.claim_id,
        )
    return result


def _validate_project_and_build(
    *,
    response: Mapping[str, object],
    request: LocalEvidenceProbeRequestV1,
    query_plan: LocalEvidenceQueryPlanV1,
    plan_sha256: str,
    kb_root: Path,
    source_snapshot_sha256: str,
    source_accessor: LocalKBSourceAccessor,
    resolver_context: EvidenceResolverContext,
    resolver: Callable[..., Mapping[str, object]],
) -> tuple[LocalEvidenceProbeV1, ProjectionResultV1]:
    built: tuple[LocalEvidenceProbeV1, ProjectionResultV1] | None = None
    failure_code: ReadOnlyErrorCode | None = None
    try:
        validated = validate_two_stage_response(
            response,
            request=request,
            plan=query_plan,
        )
        projection = project_citable_references(
            validated=validated,
            request=request,
            kb_root=kb_root,
            passage_loader=source_accessor,
            resolver_context=resolver_context,
            resolver=resolver,
        )
        built = (
            _build_probe(
                query_plan=query_plan,
                request=request,
                plan_sha256=plan_sha256,
                source_snapshot_sha256=source_snapshot_sha256,
                validated=validated,
                projection=projection,
            ),
            projection,
        )
    except ReadOnlyAdapterError as exc:
        failure_code = exc.code
    except Exception:
        failure_code = ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED
    if failure_code is not None:
        _safe_failure(failure_code, failed_claim_id=request.claim_id)
    if built is None:
        _safe_failure(
            ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED,
            failed_claim_id=request.claim_id,
        )
    return built


def _postflight(source_accessor: LocalKBSourceAccessor) -> None:
    failure_code: ReadOnlyErrorCode | None = None
    try:
        source_accessor.assert_unchanged()
    except ReadOnlyAdapterError as exc:
        failure_code = exc.code
    except Exception:
        failure_code = ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED
    if failure_code is not None:
        _safe_failure(failure_code)


def build_local_evidence_probes(
    *,
    audit_bundle: ExternalAuditBundleV1,
    query_plan: LocalEvidenceQueryPlanV1,
    plan_sha256: str,
    retriever: ReadOnlyTwoStageRetriever,
    kb_root: Path,
    source_snapshot: LocalKBSourceSnapshotV1,
    source_snapshot_sha256: str,
    source_accessor: LocalKBSourceAccessor,
    resolver_context: EvidenceResolverContext,
    resolver: Callable[..., Mapping[str, object]] = resolve_evidence,
) -> tuple[LocalEvidenceProbeV1, ...]:
    """Build one all-or-nothing batch of deterministic context-only probes."""

    _preflight(
        audit_bundle=audit_bundle,
        query_plan=query_plan,
        plan_sha256=plan_sha256,
        retriever=retriever,
        kb_root=kb_root,
        source_snapshot=source_snapshot,
        source_snapshot_sha256=source_snapshot_sha256,
        source_accessor=source_accessor,
    )
    probes: list[LocalEvidenceProbeV1] = []
    reference_registry: dict[str, tuple[str, str, str]] = {}
    for request in query_plan.requests:
        response = _retrieve(
            retriever=retriever,
            request=request,
            query_plan=query_plan,
        )
        probe, projection = _validate_project_and_build(
            response=response,
            request=request,
            query_plan=query_plan,
            plan_sha256=plan_sha256,
            kb_root=kb_root,
            source_snapshot_sha256=source_snapshot_sha256,
            source_accessor=source_accessor,
            resolver_context=resolver_context,
            resolver=resolver,
        )
        collision = False
        for reference in projection.references:
            identity = (
                request.claim_id,
                reference.evidence_locator,
                reference.evidence_sha256,
            )
            existing = reference_registry.get(reference.evidence_ref_id)
            if existing is not None and existing != identity:
                collision = True
                break
            reference_registry[reference.evidence_ref_id] = identity
        if collision:
            _safe_failure(
                ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED,
                failed_claim_id=request.claim_id,
            )
        probes.append(probe)
    _postflight(source_accessor)
    return tuple(probes)
