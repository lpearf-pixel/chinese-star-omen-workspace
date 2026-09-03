from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.video_pipeline.contracts.external_media_v1 import ExternalAuditBundleV1
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalEvidenceQueryPlanV1,
    LocalKBSourceSnapshotV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
    bind_production_query_plan_to_audit,
    bind_source_snapshot_to_plan,
    canonical_contract_sha256,
)


def _audit_payload() -> dict[str, object]:
    return {
        "schema_version": "external-audit-bundle/v1",
        "source": {
            "schema_version": "external-media-source/v1",
            "source_id": "source:one",
            "platform": "other",
            "creator_id": "creator:one",
            "creator_display_name": "Fixture",
            "creator_account_locator": "fixture-account",
            "platform_work_id": "work-1",
            "fixed_url": "https://example.test/work-1",
            "published_at_utc": "2026-01-01T00:00:00Z",
            "capture_status": "metadata_only",
            "captures": [
                {
                    "capture_id": "capture:one",
                    "capture_type": "description",
                    "content_sha256": "a" * 64,
                    "content_locator": "fixture://capture",
                    "captured_at_utc": "2026-01-01T00:00:00Z",
                    "rights_status": "metadata_only",
                    "rights_note": "research only",
                }
            ],
            "capture_notes": [],
        },
        "claims": [
            {
                "schema_version": "external-claim/v1",
                "claim_id": "claim:one",
                "source_id": "source:one",
                "claim_class": "historical_correspondence",
                "source_span": {
                    "capture_id": "capture:one",
                    "capture_sha256": "a" * 64,
                    "source_locator": "fixture://capture#chars=0-1",
                    "exact_text": "x",
                    "start_offset": 0.0,
                    "end_offset": 1.0,
                    "offset_unit": "unicode_codepoints",
                },
                "review_status": "candidate",
                "reviewer_id": None,
                "review_notes": [],
            }
        ],
        "evidence_links": [],
        "audit": {
            "schema_version": "external-audit/v1",
            "audit_id": "audit:one",
            "source_id": "source:one",
            "claim_ids": ["claim:one"],
            "evidence_link_ids": [],
            "assessments": [
                {
                    "claim_id": "claim:one",
                    "disposition": "source_missing",
                    "evidence_link_ids": [],
                    "rationale": "No source was captured.",
                }
            ],
            "overall_disposition": "source_missing",
            "research_only": True,
            "grants_rule_authority": False,
            "grants_classical_authority": False,
            "review_status": "candidate",
            "reviewer_id": None,
            "review_notes": [],
        },
    }


def _request(claim_id: str = "claim:one") -> dict[str, object]:
    return {
        "request_id": f"request:{claim_id.rsplit(':', 1)[-1]}",
        "source_id": "source:one",
        "audit_id": "audit:one",
        "claim_id": claim_id,
        "query": "fixture query",
        "kb_book_id": "kaiyuan_zhanjing",
        "query_mode": "evidence",
        "top_k": 2,
    }


def _plan_payload(*, live: bool = True) -> dict[str, object]:
    return {
        "schema_version": "local-evidence-query-plan/v1",
        "plan_id": "plan:one",
        "policy_version": "vfl-readonly-probe/1.0.0",
        "source_id": "source:one",
        "audit_id": "audit:one",
        "execution_scope": "reviewed_live" if live else "hermetic_test",
        "collection": "local_kb_kaiyuan_v2" if live else "test_vfl_ephemeral_one",
        "kb_book_id": "kaiyuan_zhanjing",
        "expected_corpus_version": "20260101T000000Z",
        "requests": [_request()],
    }


def _snapshot_payload(
    *,
    collection: str = "local_kb_kaiyuan_v2",
    kb_book_id: str = "kaiyuan_zhanjing",
    corpus_version: str = "20260101T000000Z",
) -> dict[str, object]:
    files = [
        {
            "relative_path": "唐開元占經/分卷/卷一.md",
            "size_bytes": 1,
            "sha256": "b" * 64,
        }
    ]
    tree_sha256 = hashlib.sha256(
        json.dumps(
            files, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "local-kb-source-snapshot/v1",
        "snapshot_id": "snapshot:one",
        "corpus_version": corpus_version,
        "collection": collection,
        "kb_book_id": kb_book_id,
        "files": files,
        "tree_sha256": tree_sha256,
    }


def test_plan_is_closed_strict_and_canonical() -> None:
    payload = _plan_payload()
    model = LocalEvidenceQueryPlanV1.model_validate(payload)
    assert isinstance(model.requests, tuple)
    assert canonical_contract_sha256(model) == hashlib.sha256(
        json.dumps(
            model.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    for mutation in (
        {"unexpected": "no"},
        {"expected_corpus_version": " 20260101T000000Z"},
        {"expected_corpus_version": "20260230T000000Z"},
        {"execution_scope": "unknown"},
        {"collection": "local_kb_default"},
    ):
        invalid = deepcopy(payload)
        invalid.update(mutation)
        with pytest.raises(ValidationError):
            LocalEvidenceQueryPlanV1.model_validate(invalid)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("query", "   "),
        ("query", 7),
        ("request_id", 7),
        ("top_k", True),
        ("top_k", "2"),
        ("top_k", 0),
        ("top_k", 21),
    ],
)
def test_request_coercion_and_bounds_are_rejected(field: str, value: object) -> None:
    payload = _plan_payload()
    payload["requests"][0][field] = value  # type: ignore[index]
    with pytest.raises(ValidationError):
        LocalEvidenceQueryPlanV1.model_validate(payload)


def test_plan_rejects_duplicate_request_and_claim_ids_independently() -> None:
    payload = _plan_payload()
    second = _request("claim:two")
    second["request_id"] = "request:one"
    payload["requests"] = [_request(), second]
    with pytest.raises(ValidationError):
        LocalEvidenceQueryPlanV1.model_validate(payload)

    payload = _plan_payload()
    second = _request()
    second["request_id"] = "request:two"
    payload["requests"] = [_request(), second]
    with pytest.raises(ValidationError):
        LocalEvidenceQueryPlanV1.model_validate(payload)


def test_plan_rejects_mixed_identity_and_crossed_scope() -> None:
    payload = _plan_payload()
    payload["requests"][0]["source_id"] = "source:two"  # type: ignore[index]
    with pytest.raises(ValidationError):
        LocalEvidenceQueryPlanV1.model_validate(payload)

    payload = _plan_payload(live=False)
    payload["collection"] = "local_kb_kaiyuan_v2"
    with pytest.raises(ValidationError):
        LocalEvidenceQueryPlanV1.model_validate(payload)


@pytest.mark.parametrize(
    "version",
    ["20260101T000000Z", "2026-01-01T000000Z"],
)
def test_corpus_version_accepts_only_real_producer_timestamps(version: str) -> None:
    payload = _plan_payload()
    payload["expected_corpus_version"] = version
    assert LocalEvidenceQueryPlanV1.model_validate(payload).expected_corpus_version == version


@pytest.mark.parametrize(
    "version",
    ["20260101T000000Z=bad", "20260101T000000Z/x", "20260101T246000Z", "20260101T000000Z\n"],
)
def test_corpus_version_rejects_noncanonical_values(version: str) -> None:
    payload = _plan_payload()
    payload["expected_corpus_version"] = version
    with pytest.raises(ValidationError):
        LocalEvidenceQueryPlanV1.model_validate(payload)


def test_snapshot_is_closed_sorted_and_hash_bound() -> None:
    payload = _snapshot_payload()
    snapshot = LocalKBSourceSnapshotV1.model_validate(payload)
    assert isinstance(snapshot.files, tuple)

    for path in ("/唐開元占經/分卷/卷一.md", "唐開元占經/分卷/../卷一.md", "wrong/卷一.md"):
        invalid = _snapshot_payload()
        invalid["files"][0]["relative_path"] = path  # type: ignore[index]
        with pytest.raises(ValidationError):
            LocalKBSourceSnapshotV1.model_validate(invalid)

    invalid = _snapshot_payload()
    invalid["files"][0]["size_bytes"] = "1"  # type: ignore[index]
    with pytest.raises(ValidationError):
        LocalKBSourceSnapshotV1.model_validate(invalid)

    invalid = _snapshot_payload()
    invalid["files"][0]["sha256"] = 1  # type: ignore[index]
    with pytest.raises(ValidationError):
        LocalKBSourceSnapshotV1.model_validate(invalid)


def test_plan_audit_and_snapshot_bindings_are_exact() -> None:
    audit = ExternalAuditBundleV1.model_validate(_audit_payload())
    plan = LocalEvidenceQueryPlanV1.model_validate(_plan_payload())
    bind_production_query_plan_to_audit(plan=plan, audit_bundle=audit)
    bind_source_snapshot_to_plan(
        snapshot=LocalKBSourceSnapshotV1.model_validate(_snapshot_payload()), plan=plan
    )

    for field, value in (
        ("collection", "other"),
        ("kb_book_id", "other-book"),
        ("corpus_version", "20260102T000000Z"),
    ):
        with pytest.raises(ReadOnlyAdapterError) as caught:
            bind_source_snapshot_to_plan(
                snapshot=LocalKBSourceSnapshotV1.model_validate(
                    _snapshot_payload(**{field: value})
                ),
                plan=plan,
            )
        assert caught.value.code is ReadOnlyErrorCode.SNAPSHOT_MISMATCH

    hermetic = LocalEvidenceQueryPlanV1.model_validate(_plan_payload(live=False))
    with pytest.raises(ReadOnlyAdapterError) as caught:
        bind_production_query_plan_to_audit(plan=hermetic, audit_bundle=audit)
    assert caught.value.code is ReadOnlyErrorCode.PLAN_MISMATCH


@pytest.mark.parametrize("mismatch", ["source", "audit", "claims"])
def test_production_binder_rejects_each_audit_identity_mismatch(mismatch: str) -> None:
    payload = _audit_payload()
    if mismatch == "source":
        payload["source"]["source_id"] = "source:two"  # type: ignore[index]
        payload["claims"][0]["source_id"] = "source:two"  # type: ignore[index]
        payload["audit"]["source_id"] = "source:two"  # type: ignore[index]
    elif mismatch == "audit":
        payload["audit"]["audit_id"] = "audit:two"  # type: ignore[index]
    else:
        payload["claims"][0]["claim_id"] = "claim:two"  # type: ignore[index]
        payload["audit"]["claim_ids"] = ["claim:two"]  # type: ignore[index]
        payload["audit"]["assessments"][0]["claim_id"] = "claim:two"  # type: ignore[index]
    audit = ExternalAuditBundleV1.model_validate(payload)
    with pytest.raises(ReadOnlyAdapterError) as caught:
        bind_production_query_plan_to_audit(
            plan=LocalEvidenceQueryPlanV1.model_validate(_plan_payload()),
            audit_bundle=audit,
        )
    assert caught.value.code is ReadOnlyErrorCode.PLAN_MISMATCH
