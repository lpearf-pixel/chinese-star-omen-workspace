from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.video_pipeline.contracts import ExternalAuditBundleV1
from tests.video_pipeline.external_media.helpers import valid_bundle_payload


def test_valid_external_audit_bundle_closes_all_references() -> None:
    bundle = ExternalAuditBundleV1.model_validate(valid_bundle_payload())
    assert bundle.audit.source_id == bundle.source.source_id
    assert bundle.claims[0].source_span.capture_sha256 == "a" * 64


@pytest.mark.parametrize("target", ["claim_source", "audit_source"])
def test_bundle_rejects_cross_source_references(target: str) -> None:
    payload = valid_bundle_payload()
    if target == "claim_source":
        payload["claims"][0]["source_id"] = "media:fixture:other"
    else:
        payload["audit"]["source_id"] = "media:fixture:other"

    with pytest.raises(ValidationError, match="source_id"):
        ExternalAuditBundleV1.model_validate(payload)


@pytest.mark.parametrize("mutation", ["capture_id", "capture_sha256"])
def test_claim_span_must_bind_to_same_source_capture(mutation: str) -> None:
    payload = valid_bundle_payload()
    payload["claims"][0]["source_span"][mutation] = (
        "capture:fixture:missing" if mutation == "capture_id" else "c" * 64
    )

    with pytest.raises(ValidationError, match="source capture"):
        ExternalAuditBundleV1.model_validate(payload)


def test_bundle_rejects_dangling_or_unlisted_claim_and_evidence_ids() -> None:
    dangling_claim = valid_bundle_payload()
    dangling_claim["evidence_links"][0]["claim_id"] = "claim:fixture:missing"
    with pytest.raises(ValidationError, match="unknown claim"):
        ExternalAuditBundleV1.model_validate(dangling_claim)

    omitted_claim = valid_bundle_payload()
    omitted_claim["audit"]["claim_ids"] = ["claim:fixture:other"]
    omitted_claim["audit"]["assessments"][0]["claim_id"] = "claim:fixture:other"
    with pytest.raises(ValidationError, match="exactly list bundle claims"):
        ExternalAuditBundleV1.model_validate(omitted_claim)

    omitted_evidence = valid_bundle_payload()
    omitted_evidence["audit"]["evidence_link_ids"] = []
    omitted_evidence["audit"]["assessments"][0]["evidence_link_ids"] = []
    with pytest.raises(ValidationError, match="exactly list bundle evidence"):
        ExternalAuditBundleV1.model_validate(omitted_evidence)


def test_supported_exact_requires_unqualified_support_of_matching_evidence_class() -> None:
    no_support = valid_bundle_payload()
    no_support["audit"]["assessments"][0]["disposition"] = "supported_exact"
    no_support["audit"]["overall_disposition"] = "supported_exact"
    no_support["evidence_links"][0]["relationship"] = "context_only"
    with pytest.raises(ValidationError, match="supported_exact"):
        ExternalAuditBundleV1.model_validate(no_support)

    wrong_class = valid_bundle_payload()
    wrong_class["claims"][0]["claim_class"] = "astronomy_fact"
    wrong_class["audit"]["assessments"][0]["disposition"] = "supported_exact"
    wrong_class["audit"]["overall_disposition"] = "supported_exact"
    with pytest.raises(ValidationError, match="matching evidence class"):
        ExternalAuditBundleV1.model_validate(wrong_class)

    contradicted_too = valid_bundle_payload()
    contradicted_too["audit"]["assessments"][0]["disposition"] = "supported_exact"
    contradicted_too["audit"]["overall_disposition"] = "supported_exact"
    contradiction = deepcopy(contradicted_too["evidence_links"][0])
    contradiction["evidence_link_id"] = "evidence-link:fixture:002"
    contradiction["relationship"] = "contradicts"
    contradicted_too["evidence_links"].append(contradiction)
    contradicted_too["audit"]["evidence_link_ids"].append(
        contradiction["evidence_link_id"]
    )
    contradicted_too["audit"]["assessments"][0]["evidence_link_ids"].append(
        contradiction["evidence_link_id"]
    )
    with pytest.raises(ValidationError, match="contradicting"):
        ExternalAuditBundleV1.model_validate(contradicted_too)


def test_contradicted_requires_an_explicit_contradicting_link() -> None:
    payload = valid_bundle_payload()
    payload["audit"]["assessments"][0]["disposition"] = "contradicted"
    payload["audit"]["overall_disposition"] = "contradicted"

    with pytest.raises(ValidationError, match="contradicted"):
        ExternalAuditBundleV1.model_validate(payload)


def test_source_missing_cannot_carry_synthetic_evidence() -> None:
    payload = valid_bundle_payload()
    payload["audit"]["assessments"][0]["disposition"] = "source_missing"
    payload["audit"]["overall_disposition"] = "source_missing"

    with pytest.raises(ValidationError, match="source_missing"):
        ExternalAuditBundleV1.model_validate(payload)


def test_modern_inference_only_rejects_non_modern_evidence() -> None:
    payload = valid_bundle_payload()
    payload["evidence_links"][0]["evidence_class"] = "classical_passage"

    with pytest.raises(ValidationError, match="modern_inference_only"):
        ExternalAuditBundleV1.model_validate(payload)


def test_partial_requires_supporting_or_qualifying_evidence() -> None:
    payload = valid_bundle_payload()
    payload["audit"]["assessments"][0]["disposition"] = "partial"
    payload["audit"]["overall_disposition"] = "partial"
    payload["evidence_links"][0]["relationship"] = "context_only"

    with pytest.raises(ValidationError, match="partial"):
        ExternalAuditBundleV1.model_validate(payload)


def test_single_disposition_must_equal_overall_disposition() -> None:
    payload = valid_bundle_payload()
    payload["audit"]["overall_disposition"] = "ambiguous"

    with pytest.raises(ValidationError, match="overall_disposition"):
        ExternalAuditBundleV1.model_validate(payload)
