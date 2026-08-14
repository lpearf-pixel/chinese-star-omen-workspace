from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.video_pipeline.contracts import (
    EvidenceLinkV1,
    ExternalAuditV1,
    ExternalClaimV1,
    ExternalMediaSourceV1,
)
from tests.video_pipeline.external_media.helpers import (
    valid_audit_payload,
    valid_claim_payload,
    valid_evidence_link_payload,
    valid_source_payload,
)


@pytest.mark.parametrize(
    ("model", "payload_factory"),
    [
        (ExternalMediaSourceV1, valid_source_payload),
        (ExternalClaimV1, valid_claim_payload),
        (EvidenceLinkV1, valid_evidence_link_payload),
        (ExternalAuditV1, valid_audit_payload),
    ],
)
def test_external_media_contracts_accept_strict_valid_payloads(
    model: type, payload_factory
) -> None:
    instance = model.model_validate(payload_factory())
    assert instance.schema_version.endswith("/v1")


@pytest.mark.parametrize(
    ("model", "payload_factory"),
    [
        (ExternalMediaSourceV1, valid_source_payload),
        (ExternalClaimV1, valid_claim_payload),
        (EvidenceLinkV1, valid_evidence_link_payload),
        (ExternalAuditV1, valid_audit_payload),
    ],
)
def test_external_media_contracts_reject_unknown_fields(
    model: type, payload_factory
) -> None:
    payload = payload_factory()
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_capture_state_cannot_contradict_capture_inventory() -> None:
    captured_without_bytes = valid_source_payload()
    captured_without_bytes["captures"] = []
    with pytest.raises(ValidationError, match="captured source requires captures"):
        ExternalMediaSourceV1.model_validate(captured_without_bytes)

    missing_with_bytes = valid_source_payload()
    missing_with_bytes["capture_status"] = "source_missing"
    with pytest.raises(ValidationError, match="source_missing cannot contain captures"):
        ExternalMediaSourceV1.model_validate(missing_with_bytes)


def test_source_times_are_explicit_utc_and_capture_ids_are_unique() -> None:
    non_utc = valid_source_payload()
    non_utc["published_at_utc"] = "2026-08-12T09:00:00+08:00"
    with pytest.raises(ValidationError):
        ExternalMediaSourceV1.model_validate(non_utc)

    duplicate = valid_source_payload()
    duplicate["captures"].append(deepcopy(duplicate["captures"][0]))
    with pytest.raises(ValidationError, match="captures"):
        ExternalMediaSourceV1.model_validate(duplicate)


def test_claim_span_requires_exact_hash_and_ordered_offsets() -> None:
    bad_hash = valid_claim_payload()
    bad_hash["source_span"]["capture_sha256"] = "not-a-hash"
    with pytest.raises(ValidationError):
        ExternalClaimV1.model_validate(bad_hash)

    reversed_span = valid_claim_payload()
    reversed_span["source_span"]["end_offset"] = 0.0
    with pytest.raises(ValidationError, match="end_offset"):
        ExternalClaimV1.model_validate(reversed_span)

    fractional_char = valid_claim_payload()
    fractional_char["source_span"]["start_offset"] = 0.5
    with pytest.raises(ValidationError, match="integer offsets"):
        ExternalClaimV1.model_validate(fractional_char)


@pytest.mark.parametrize(
    ("model", "payload_factory"),
    [
        (ExternalClaimV1, valid_claim_payload),
        (EvidenceLinkV1, valid_evidence_link_payload),
        (ExternalAuditV1, valid_audit_payload),
    ],
)
def test_human_review_state_requires_reviewer_identity(model: type, payload_factory) -> None:
    payload = payload_factory()
    payload["review_status"] = "human_verified"
    with pytest.raises(ValidationError, match="reviewer_id"):
        model.model_validate(payload)


def test_audit_requires_exact_claim_coverage_and_unique_references() -> None:
    missing_assessment = valid_audit_payload()
    missing_assessment["assessments"] = []
    with pytest.raises(ValidationError, match="exactly cover"):
        ExternalAuditV1.model_validate(missing_assessment)

    duplicate = valid_audit_payload()
    duplicate["claim_ids"].append(duplicate["claim_ids"][0])
    with pytest.raises(ValidationError, match="claim_ids"):
        ExternalAuditV1.model_validate(duplicate)

    dangling = valid_audit_payload()
    dangling["assessments"][0]["evidence_link_ids"] = [
        "evidence-link:fixture:missing"
    ]
    with pytest.raises(ValidationError, match="audit evidence_link_ids"):
        ExternalAuditV1.model_validate(dangling)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("research_only", False),
        ("grants_rule_authority", True),
        ("grants_classical_authority", True),
    ],
)
def test_audit_safety_flags_cannot_be_disabled(field: str, value: bool) -> None:
    payload = valid_audit_payload()
    payload[field] = value
    with pytest.raises(ValidationError):
        ExternalAuditV1.model_validate(payload)
