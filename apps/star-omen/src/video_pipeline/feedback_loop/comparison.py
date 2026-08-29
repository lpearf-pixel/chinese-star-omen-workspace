from __future__ import annotations

from typing import Sequence

from src.video_pipeline.contracts.external_media_v1 import ExternalAuditBundleV1
from src.video_pipeline.feedback_loop.contracts_v1 import (
    FeedbackObservationV1,
    LocalEvidenceProbeV1,
    OperationalDisposition,
)


def compare_external_audit(
    *,
    audit_bundle: ExternalAuditBundleV1,
    local_probes: Sequence[LocalEvidenceProbeV1],
) -> tuple[FeedbackObservationV1, ...]:
    """Compare one validated external audit with complete read-only local probes."""
    audit = ExternalAuditBundleV1.model_validate(audit_bundle.model_dump(mode="python"))
    probes = [
        LocalEvidenceProbeV1.model_validate(probe.model_dump(mode="python"))
        for probe in local_probes
    ]
    probes.sort(key=lambda probe: probe.claim_id)

    probes_by_claim_id: dict[str, LocalEvidenceProbeV1] = {}
    for probe in probes:
        if probe.claim_id in probes_by_claim_id:
            raise ValueError(f"duplicate probe for claim_id {probe.claim_id}")
        if probe.claim_id not in set(audit.audit.claim_ids):
            raise ValueError(f"probe references unknown claim_id {probe.claim_id}")
        if probe.source_id != audit.source.source_id:
            raise ValueError("probe source_id must equal audit source_id")
        probes_by_claim_id[probe.claim_id] = probe

    audit_claim_ids = set(audit.audit.claim_ids)
    if set(probes_by_claim_id) != audit_claim_ids:
        raise ValueError("local probe coverage must exactly match audit claim_ids")

    links_by_id = {
        link.evidence_link_id: link for link in audit.evidence_links
    }
    observations: list[FeedbackObservationV1] = []
    for assessment in sorted(audit.audit.assessments, key=lambda item: item.claim_id):
        probe = probes_by_claim_id[assessment.claim_id]
        external_evidence_link_ids = sorted(assessment.evidence_link_ids)
        local_evidence_ref_ids = sorted(
            reference.evidence_ref_id for reference in probe.evidence_references
        )
        context_only = any(
            links_by_id[link_id].evidence_class == "modern_authority"
            and links_by_id[link_id].relationship == "context_only"
            for link_id in external_evidence_link_ids
        )
        operational_disposition = _operational_disposition(
            external_disposition=assessment.disposition,
            local_result_state=probe.result_state,
            context_only=context_only,
        )
        observations.append(
            FeedbackObservationV1(
                observation_id=(
                    f"observation:{audit.audit.audit_id}:{assessment.claim_id}"
                ),
                source_id=audit.source.source_id,
                audit_id=audit.audit.audit_id,
                claim_id=assessment.claim_id,
                probe_id=probe.probe_id,
                external_disposition=assessment.disposition,
                local_result_state=probe.result_state,
                operational_disposition=operational_disposition,
                external_evidence_link_ids=external_evidence_link_ids,
                local_evidence_ref_ids=local_evidence_ref_ids,
                rationale=(
                    "Operational disposition is a deterministic comparison of "
                    "the preserved external audit and the caller-supplied local probe."
                ),
            )
        )
    return tuple(observations)


def _operational_disposition(
    *,
    external_disposition: str,
    local_result_state: str,
    context_only: bool,
) -> OperationalDisposition:
    if local_result_state == "not_searched":
        return "not_searched"
    if context_only or external_disposition == "modern_inference_only":
        return "modern_context_only"
    if local_result_state == "contradicted":
        return "contradicted"
    if local_result_state == "corroborated":
        return "supported"
    if external_disposition == "source_missing":
        return "source_missing"
    if external_disposition == "supported_exact":
        return "supported"
    if external_disposition == "contradicted":
        return "contradicted"
    if external_disposition in {"partial", "ambiguous"}:
        return "ambiguous"
    raise ValueError(f"unsupported external disposition {external_disposition}")
