from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

import src.video_pipeline.feedback_loop.readonly_adapter_v1 as adapter_module
from src.connectors.evidence_resolver import EvidenceResolverContext, resolve_evidence
from src.video_pipeline.feedback_loop.orchestrator import build_feedback_loop_run
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalEvidenceQueryPlanV1,
    LocalKBSourceSnapshotV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
    SourceSnapshotBindingV1,
    canonical_contract_sha256,
)
from src.video_pipeline.feedback_loop.readonly_runtime_v1 import (
    build_local_evidence_probes,
)
from src.video_pipeline.feedback_loop.source_snapshot_v1 import LocalKBSourceAccessor
from tests.video_pipeline.feedback_loop.test_comparison_v1 import (
    CLAIM_IDS,
    load_episode_22_audit,
)
from tests.video_pipeline.feedback_loop.test_readonly_adapter_v1 import (
    BOOK_ID,
    COLLECTION,
    CONTEXT,
    CORPUS_VERSION,
    PROVENANCE,
    RAW_TEXT,
    RELATIVE_PATH,
    _hit,
    _response,
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _plan(*, query_suffix: str = "") -> LocalEvidenceQueryPlanV1:
    audit = load_episode_22_audit()
    return LocalEvidenceQueryPlanV1.model_validate(
        {
            "schema_version": "local-evidence-query-plan/v1",
            "plan_id": "plan:task4-runtime",
            "policy_version": "vfl-readonly-probe/1.0.0",
            "source_id": audit.source.source_id,
            "audit_id": audit.audit.audit_id,
            "execution_scope": "hermetic_test",
            "collection": COLLECTION,
            "kb_book_id": BOOK_ID,
            "expected_corpus_version": CORPUS_VERSION,
            "requests": [
                {
                    "request_id": f"request:{claim_id.rsplit(':', 1)[-1]}",
                    "source_id": audit.source.source_id,
                    "audit_id": audit.audit.audit_id,
                    "claim_id": claim_id,
                    "query": f"query {index}{query_suffix}",
                    "kb_book_id": BOOK_ID,
                    "query_mode": "evidence",
                    "top_k": 4,
                }
                for index, claim_id in enumerate(CLAIM_IDS, start=1)
            ],
        }
    )


def _tree_hash(files: list[dict[str, object]]) -> str:
    return hashlib.sha256(_canonical(files)).hexdigest()


def _source_snapshot(root: Path) -> LocalKBSourceSnapshotV1:
    source = root / RELATIVE_PATH
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        f"# 唐開元占經\n<pb:KR3g0018_WYG_031-17a>\n{RAW_TEXT}\n",
        encoding="utf-8",
    )
    raw = source.read_bytes()
    files: list[dict[str, object]] = [
        {
            "relative_path": RELATIVE_PATH,
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    ]
    return LocalKBSourceSnapshotV1.model_validate(
        {
            "schema_version": "local-kb-source-snapshot/v1",
            "snapshot_id": "snapshot:task4-runtime",
            "corpus_version": CORPUS_VERSION,
            "collection": COLLECTION,
            "kb_book_id": BOOK_ID,
            "files": files,
            "tree_sha256": _tree_hash(files),
        }
    )


class _RecordingRetriever:
    _FORBIDDEN = frozenset(("ingest", "upsert", "delete", "promote", "sync"))

    def __init__(
        self,
        *,
        binding: SourceSnapshotBindingV1,
        responses: list[object] | None = None,
    ) -> None:
        self.source_binding = binding
        self.responses = responses or [_response(), _response()]
        self.calls: list[tuple[str, dict[str, object]]] = []

    def two_stage_retrieve(self, query: str, **kwargs: object):
        self.calls.append((query, dict(kwargs)))
        value = self.responses[len(self.calls) - 1]
        if isinstance(value, BaseException):
            raise value
        return deepcopy(value)

    def __getattr__(self, name: str):
        if name in self._FORBIDDEN:
            raise AssertionError(f"forbidden mutation member accessed: {name}")
        raise AttributeError(name)


def _build(
    *,
    root: Path,
    snapshot: LocalKBSourceSnapshotV1,
    accessor: LocalKBSourceAccessor,
    retriever: _RecordingRetriever,
    plan: LocalEvidenceQueryPlanV1 | None = None,
    plan_sha256: str | None = None,
    snapshot_sha256: str | None = None,
    context: EvidenceResolverContext = CONTEXT,
    resolver=resolve_evidence,
):
    query_plan = plan or _plan()
    return build_local_evidence_probes(
        audit_bundle=load_episode_22_audit(),
        query_plan=query_plan,
        plan_sha256=plan_sha256 or canonical_contract_sha256(query_plan),
        retriever=retriever,
        kb_root=root,
        source_snapshot=snapshot,
        source_snapshot_sha256=snapshot_sha256 or canonical_contract_sha256(snapshot),
        source_accessor=accessor,
        resolver_context=context,
        resolver=resolver,
    )


def test_runtime_calls_only_two_stage_in_canonical_claim_order_and_builds_exact_probes(
    tmp_path: Path,
) -> None:
    """Catches reordered calls, mutable partial output, and noncanonical probe metadata."""

    plan = _plan()
    snapshot = _source_snapshot(tmp_path)
    with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
        retriever = _RecordingRetriever(binding=accessor.binding)
        probes = _build(
            root=tmp_path,
            snapshot=snapshot,
            accessor=accessor,
            retriever=retriever,
            plan=plan,
        )

    assert isinstance(probes, tuple)
    assert [probe.claim_id for probe in probes] == list(CLAIM_IDS)
    assert retriever.calls == [
        (
            request.query,
            {
                "top_k": request.top_k,
                "collection": plan.collection,
                "filters": {"kb_book_id": request.kb_book_id},
                "query_mode": "evidence",
            },
        )
        for request in plan.requests
    ]
    assert all(probe.result_state == "unresolved" for probe in probes)
    assert all(
        reference.relationship == "context_only"
        for probe in probes
        for reference in probe.evidence_references
    )
    expected_rejections = [
        "rejected.candidate_only=0",
        "rejected.source_outside_root=0",
        "rejected.missing_source=0",
        "rejected.book_mismatch=0",
        "rejected.card_type_mismatch=0",
        "rejected.locator_mismatch=0",
        "rejected.page_mismatch=0",
        "rejected.paragraph_mismatch=0",
        "rejected.heading_mismatch=0",
        "rejected.anchor_mismatch=0",
        "rejected.hash_mismatch=0",
    ]
    assert probes[0].notes == [
        f"plan_id={plan.plan_id}",
        f"request_id={plan.requests[0].request_id}",
        f"collection={COLLECTION}",
        f"expected_corpus_version={CORPUS_VERSION}",
        f"observed_corpus_version={CORPUS_VERSION}",
        f"upstream_provenance_sha256={PROVENANCE}",
        "corpus_provenance=upstream_meta",
        "top_k=4",
        "exact_candidate_count=1",
        "citable_count=1",
        f"source_snapshot_sha256={canonical_contract_sha256(snapshot)}",
        *expected_rejections,
    ]

    request = plan.requests[0]
    reference_payloads = [
        item.model_dump(mode="json") for item in probes[0].evidence_references
    ]
    probe_preimage = {
        "policy_version": plan.policy_version,
        "plan_sha256": canonical_contract_sha256(plan),
        "plan_id": plan.plan_id,
        "execution_scope": plan.execution_scope,
        "request_id": request.request_id,
        "source_id": request.source_id,
        "claim_id": request.claim_id,
        "query": request.query,
        "top_k": request.top_k,
        "collection": plan.collection,
        "expected_corpus_version": plan.expected_corpus_version,
        "observed_corpus_version": CORPUS_VERSION,
        "upstream_provenance_sha256": PROVENANCE,
        "corpus_provenance": "upstream_meta",
        "source_snapshot_sha256": canonical_contract_sha256(snapshot),
        "response_schema_versions": [
            "kb-retrieve/v2",
            "kb-two-stage/v2",
            "kb-retrieve/v2",
        ],
        "evidence_references": reference_payloads,
    }
    assert probes[0].probe_id == (
        "probe:vfl:s1:" + hashlib.sha256(_canonical(probe_preimage)).hexdigest()
    )
    retrieval_preimage = {
        "policy_version": plan.policy_version,
        "plan_sha256": canonical_contract_sha256(plan),
        "upstream_provenance_sha256": PROVENANCE,
        "corpus_provenance": "upstream_meta",
        "source_snapshot_sha256": canonical_contract_sha256(snapshot),
        "response_schema_versions": [
            "kb-retrieve/v2",
            "kb-two-stage/v2",
            "kb-retrieve/v2",
        ],
    }
    assert probes[0].retrieval_version == (
        "vfl-readonly-probe/1.0.0:sha256:"
        + hashlib.sha256(_canonical(retrieval_preimage)).hexdigest()
    )
    assert len(probes[0].retrieval_version) <= 256


def test_runtime_forwards_the_exact_resolver_context_without_global_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Catches runtime context reconstruction or a resolver fallback to global settings."""

    import src.connectors.evidence_resolver as resolver_module

    monkeypatch.setattr(
        resolver_module,
        "get_settings",
        lambda: pytest.fail("explicit resolver context must bypass global settings"),
    )
    plan = _plan()
    snapshot = _source_snapshot(tmp_path)
    seen: list[EvidenceResolverContext] = []

    def recording_resolver(evidence, kb_root, *, passage_loader, resolver_context):
        seen.append(resolver_context)
        return resolve_evidence(
            evidence,
            kb_root,
            passage_loader=passage_loader,
            resolver_context=resolver_context,
        )

    with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
        retriever = _RecordingRetriever(binding=accessor.binding)
        probes = _build(
            root=tmp_path,
            snapshot=snapshot,
            accessor=accessor,
            retriever=retriever,
            plan=plan,
            context=CONTEXT,
            resolver=recording_resolver,
        )
    assert len(probes) == 2
    assert seen == [CONTEXT, CONTEXT]
    assert all(item is CONTEXT for item in seen)


@pytest.mark.parametrize("which", ["plan_hash", "snapshot_hash", "retriever_binding"])
def test_runtime_preflight_mismatches_fail_before_first_retrieval(
    tmp_path: Path,
    which: str,
) -> None:
    """Catches delayed identity checks after observable retrieval work."""

    plan = _plan()
    snapshot = _source_snapshot(tmp_path)
    with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
        binding = accessor.binding
        if which == "retriever_binding":
            binding = replace(binding, snapshot_sha256="0" * 64)
        retriever = _RecordingRetriever(binding=binding)
        kwargs: dict[str, object] = {}
        if which == "plan_hash":
            kwargs["plan_sha256"] = "0" * 64
        if which == "snapshot_hash":
            kwargs["snapshot_sha256"] = "0" * 64
        with pytest.raises(ReadOnlyAdapterError) as caught:
            _build(
                root=tmp_path,
                snapshot=snapshot,
                accessor=accessor,
                retriever=retriever,
                plan=plan,
                **kwargs,
            )
    assert caught.value.code in {
        ReadOnlyErrorCode.PLAN_MISMATCH,
        ReadOnlyErrorCode.SNAPSHOT_MISMATCH,
    }
    assert caught.value.failed_claim_id is None
    assert retriever.calls == []


def test_second_request_failure_reports_current_claim_without_partial_tuple(
    tmp_path: Path,
) -> None:
    """Catches returning the first probe or attributing a later failure to claim one."""

    plan = _plan()
    snapshot = _source_snapshot(tmp_path)
    secret = "unsafe-upstream-detail"
    error = ReadOnlyAdapterError(ReadOnlyErrorCode.TRANSPORT_FAILED)
    error.add_note(secret)
    with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
        retriever = _RecordingRetriever(
            binding=accessor.binding,
            responses=[_response(), error],
        )
        with pytest.raises(ReadOnlyAdapterError) as caught:
            _build(
                root=tmp_path,
                snapshot=snapshot,
                accessor=accessor,
                retriever=retriever,
                plan=plan,
            )
    assert caught.value.code is ReadOnlyErrorCode.TRANSPORT_FAILED
    assert caught.value.failed_claim_id == CLAIM_IDS[1]
    assert str(caught.value) == "transport_failed"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert secret not in str(caught.value)
    assert len(retriever.calls) == 2


def test_resolver_failure_is_safe_and_bound_to_the_current_claim(tmp_path: Path) -> None:
    """Catches unsafe resolver causes or missing failed-claim attribution."""

    plan = _plan()
    snapshot = _source_snapshot(tmp_path)

    def bad_resolver(*args: object, **kwargs: object):
        raise RuntimeError("source text and /private/path")

    with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
        retriever = _RecordingRetriever(binding=accessor.binding)
        with pytest.raises(ReadOnlyAdapterError) as caught:
            _build(
                root=tmp_path,
                snapshot=snapshot,
                accessor=accessor,
                retriever=retriever,
                plan=plan,
                resolver=bad_resolver,
            )
    assert caught.value.code is ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED
    assert caught.value.failed_claim_id == CLAIM_IDS[0]
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert str(caught.value) == "evidence_projection_rejected"


def test_snapshot_postflight_failure_has_no_claim_and_no_batch_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Catches returning an in-memory batch before the final snapshot recheck."""

    plan = _plan()
    snapshot = _source_snapshot(tmp_path)
    calls = 0
    original = LocalKBSourceAccessor.assert_unchanged

    def drifting(self: LocalKBSourceAccessor) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ReadOnlyAdapterError(ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED)
        original(self)

    monkeypatch.setattr(LocalKBSourceAccessor, "assert_unchanged", drifting)
    with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
        retriever = _RecordingRetriever(binding=accessor.binding)
        with pytest.raises(ReadOnlyAdapterError) as caught:
            _build(
                root=tmp_path,
                snapshot=snapshot,
                accessor=accessor,
                retriever=retriever,
                plan=plan,
            )
    assert caught.value.code is ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED
    assert caught.value.failed_claim_id is None
    assert calls == 2


def test_duplicate_and_permuted_hits_preserve_probe_and_s0_run_identity(tmp_path: Path) -> None:
    """Catches input-order bytes or identical duplicates entering persisted identity."""

    plan = _plan()
    snapshot = _source_snapshot(tmp_path)
    ordinary = [_response(), _response()]
    permuted = []
    for response in ordinary:
        changed = deepcopy(response)
        hit = changed["stage2"]["exact_hits"][0]
        for key in ("hits", "exact_hits", "primary_candidates", "inferred_hits"):
            changed["stage2"][key] = [deepcopy(hit), hit]
        permuted.append(changed)

    batches = []
    for responses in (ordinary, permuted):
        with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
            retriever = _RecordingRetriever(binding=accessor.binding, responses=responses)
            batches.append(
                _build(
                    root=tmp_path,
                    snapshot=snapshot,
                    accessor=accessor,
                    retriever=retriever,
                    plan=plan,
                )
            )
    assert batches[0] == batches[1]
    assert build_feedback_loop_run(
        audit_bundle=load_episode_22_audit(), local_probes=batches[0]
    ).run.run_id == build_feedback_loop_run(
        audit_bundle=load_episode_22_audit(), local_probes=batches[1]
    ).run.run_id


def test_probe_and_run_identity_change_with_semantic_provenance_not_telemetry(
    tmp_path: Path,
) -> None:
    """Catches dropping semantic meta provenance or persisting run telemetry."""

    plan = _plan()
    snapshot = _source_snapshot(tmp_path)
    batches = []
    for provenance in (PROVENANCE, "d" * 64):
        responses = [_response(), _response()]
        for response in responses:
            response["stage1"]["observability"][
                "upstream_provenance_sha256"
            ] = provenance
            response["stage2"]["official_result"]["observability"][
                "upstream_provenance_sha256"
            ] = provenance
            response["observability"]["upstream_provenance_sha256"] = provenance
            response["observability"]["stages"][0][
                "upstream_provenance_sha256"
            ] = provenance
            response["observability"]["stages"][1][
                "upstream_provenance_sha256"
            ] = provenance
            response["observability"]["total_latency_ms"] = 999.0
        with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
            retriever = _RecordingRetriever(binding=accessor.binding, responses=responses)
            batches.append(
                _build(
                    root=tmp_path,
                    snapshot=snapshot,
                    accessor=accessor,
                    retriever=retriever,
                    plan=plan,
                )
            )
    assert batches[0][0].probe_id != batches[1][0].probe_id
    assert batches[0][0].retrieval_version != batches[1][0].retrieval_version
    runs = [
        build_feedback_loop_run(
            audit_bundle=load_episode_22_audit(), local_probes=batch
        ).run.run_id
        for batch in batches
    ]
    assert runs[0] != runs[1]


def test_global_reference_id_collision_across_claims_aborts_whole_batch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Catches per-claim-only collision registries allowing a reused global ID."""

    monkeypatch.setattr(
        adapter_module,
        "_reference_id",
        lambda **kwargs: "evidence:vfl:s1:" + "0" * 64,
    )
    plan = _plan()
    snapshot = _source_snapshot(tmp_path)
    with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
        retriever = _RecordingRetriever(binding=accessor.binding)
        with pytest.raises(ReadOnlyAdapterError) as caught:
            _build(
                root=tmp_path,
                snapshot=snapshot,
                accessor=accessor,
                retriever=retriever,
                plan=plan,
            )
    assert caught.value.code is ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED
    assert caught.value.failed_claim_id == CLAIM_IDS[1]


def test_plan_query_change_and_snapshot_identity_change_alter_probe_identity(
    tmp_path: Path,
) -> None:
    """Catches binding request or snapshot fields only indirectly."""

    original_plan = _plan()
    changed_plan = _plan(query_suffix=" changed")
    original_snapshot = _source_snapshot(tmp_path)
    batches = []
    for plan in (original_plan, changed_plan):
        with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=original_snapshot) as accessor:
            retriever = _RecordingRetriever(binding=accessor.binding)
            batches.append(
                _build(
                    root=tmp_path,
                    snapshot=original_snapshot,
                    accessor=accessor,
                    retriever=retriever,
                    plan=plan,
                )
            )
    assert batches[0][0].probe_id != batches[1][0].probe_id

    payload = original_snapshot.model_dump(mode="json")
    payload["snapshot_id"] = "snapshot:task4-runtime-changed"
    changed_snapshot = LocalKBSourceSnapshotV1.model_validate(payload)
    with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=changed_snapshot) as accessor:
        retriever = _RecordingRetriever(binding=accessor.binding)
        third = _build(
            root=tmp_path,
            snapshot=changed_snapshot,
            accessor=accessor,
            retriever=retriever,
            plan=original_plan,
        )
    assert batches[0][0].probe_id != third[0].probe_id
    assert batches[0][0].retrieval_version != third[0].retrieval_version
