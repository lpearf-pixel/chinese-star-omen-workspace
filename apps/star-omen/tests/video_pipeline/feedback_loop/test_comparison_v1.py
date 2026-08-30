from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.video_pipeline.contracts import ExternalAuditBundleV1
from src.video_pipeline.feedback_loop.comparison import compare_external_audit
from src.video_pipeline.feedback_loop.contracts_v1 import LocalEvidenceProbeV1
from tests.video_pipeline.feedback_loop.helpers import valid_local_probe_payload


APP_ROOT = Path(__file__).resolve().parents[3]
EPISODE_22_AUDIT_PATH = (
    APP_ROOT
    / "data"
    / "video_pipeline"
    / "external_media"
    / "祖山觀"
    / "audits"
    / "episode-22.bundle.json"
)
CLAIM_IDS = (
    "claim:douyin:zushan:episode-22:01",
    "claim:douyin:zushan:episode-22:02",
)


def load_episode_22_audit() -> ExternalAuditBundleV1:
    return ExternalAuditBundleV1.model_validate(
        json.loads(EPISODE_22_AUDIT_PATH.read_text(encoding="utf-8"))
    )


def probe_for(
    claim_id: str,
    *,
    probe_id: str | None = None,
    result_state: str = "unresolved",
    source_id: str | None = None,
    evidence_references: list[dict] | None = None,
) -> LocalEvidenceProbeV1:
    payload = valid_local_probe_payload()
    payload.update(
        {
            "probe_id": probe_id or f"probe:vfl:{claim_id.rsplit(':', 1)[-1]}",
            "claim_id": claim_id,
            "source_id": source_id
            or "media:douyin:zushan:collection-7664842437629921326:episode-22",
            "result_state": result_state,
            "evidence_references": evidence_references or [],
        }
    )
    return LocalEvidenceProbeV1.model_validate(payload)


def episode_22_probes() -> tuple[LocalEvidenceProbeV1, ...]:
    return tuple(probe_for(claim_id) for claim_id in CLAIM_IDS)


def local_reference(*, evidence_ref_id: str, relationship: str) -> dict:
    return {
        "evidence_ref_id": evidence_ref_id,
        "evidence_class": "citable_passage",
        "evidence_locator": f"fixture://local/{evidence_ref_id}",
        "evidence_sha256": "a" * 64,
        "relationship": relationship,
        "note": "Synthetic local evidence used only to exercise comparison policy.",
    }


def test_episode_22_preserves_missing_source_and_modern_context_boundary() -> None:
    """Catches a comparison that promotes unresolved or context-only material."""
    observations = compare_external_audit(
        audit_bundle=load_episode_22_audit(), local_probes=episode_22_probes()
    )

    assert [observation.claim_id for observation in observations] == list(CLAIM_IDS)
    assert observations[0].external_disposition == "source_missing"
    assert observations[0].local_result_state == "unresolved"
    assert observations[0].operational_disposition == "source_missing"
    assert observations[1].external_disposition == "ambiguous"
    assert observations[1].operational_disposition == "modern_context_only"
    assert observations[1].external_evidence_link_ids == [
        "evidence-link:douyin:zushan:episode-22:wmo-context"
    ]


def test_not_searched_probe_remains_unknown_not_a_contradiction() -> None:
    """Catches treating an unperformed local search as negative evidence."""
    probes = list(episode_22_probes())
    probes[1] = probe_for(CLAIM_IDS[1], result_state="not_searched")

    observations = compare_external_audit(
        audit_bundle=load_episode_22_audit(), local_probes=probes
    )

    observation = observations[1]
    assert observation.local_result_state == "not_searched"
    assert observation.operational_disposition == "not_searched"
    assert observation.local_evidence_ref_ids == []


@pytest.mark.parametrize(
    ("result_state", "relationship", "operational_disposition"),
    [
        ("corroborated", "supports", "supported"),
        ("contradicted", "contradicts", "contradicted"),
    ],
)
def test_explicit_local_evidence_narrows_the_context_only_claim(
    result_state: str, relationship: str, operational_disposition: str
) -> None:
    """Catches context-only policy masking explicit local evidence states."""
    evidence_ref_id = f"local-evidence:vfl:context-{result_state}"
    observations = compare_external_audit(
        audit_bundle=load_episode_22_audit(),
        local_probes=(
            probe_for(CLAIM_IDS[0]),
            probe_for(
                CLAIM_IDS[1],
                result_state=result_state,
                evidence_references=[
                    local_reference(
                        evidence_ref_id=evidence_ref_id, relationship=relationship
                    )
                ],
            ),
        ),
    )

    observation = observations[1]
    assert observation.external_disposition == "ambiguous"
    assert observation.external_evidence_link_ids == [
        "evidence-link:douyin:zushan:episode-22:wmo-context"
    ]
    assert observation.local_evidence_ref_ids == [evidence_ref_id]
    assert observation.operational_disposition == operational_disposition


@pytest.mark.parametrize(
    ("result_state", "relationship", "operational_disposition"),
    [
        ("corroborated", "supports", "supported"),
        ("contradicted", "contradicts", "contradicted"),
    ],
)
def test_explicit_local_evidence_is_preserved(
    result_state: str, relationship: str, operational_disposition: str
) -> None:
    """Catches discarding explicit local corroboration or contradiction evidence."""
    evidence_ref_id = f"local-evidence:vfl:{result_state}"
    probes = [
        probe_for(
            CLAIM_IDS[0],
            result_state=result_state,
            evidence_references=[
                local_reference(
                    evidence_ref_id=evidence_ref_id, relationship=relationship
                )
            ],
        ),
        probe_for(CLAIM_IDS[1]),
    ]

    observations = compare_external_audit(
        audit_bundle=load_episode_22_audit(), local_probes=probes
    )

    observation = observations[0]
    assert observation.local_result_state == result_state
    assert observation.operational_disposition == operational_disposition
    assert observation.local_evidence_ref_ids == [evidence_ref_id]


@pytest.mark.parametrize(
    "evidence_class",
    ["modern_authority", "retrieval_record"],
)
def test_defensive_validation_rejects_non_authoritative_corroboration(
    evidence_class: str,
) -> None:
    """Catches a mutated modern/retrieval-only probe becoming supported."""
    purported = probe_for(
        CLAIM_IDS[1],
        result_state="corroborated",
        evidence_references=[
            local_reference(
                evidence_ref_id=f"local-evidence:vfl:{evidence_class}",
                relationship="supports",
            )
        ],
    )
    object.__setattr__(
        purported.evidence_references[0], "evidence_class", evidence_class
    )

    with pytest.raises(ValueError, match="citable|historical"):
        compare_external_audit(
            audit_bundle=load_episode_22_audit(),
            local_probes=(probe_for(CLAIM_IDS[0]), purported),
        )


@pytest.mark.parametrize(
    ("probes", "error"),
    [
        (
            lambda: episode_22_probes() + (probe_for(CLAIM_IDS[0]),),
            "duplicate probe",
        ),
        (
            lambda: (
                probe_for("claim:douyin:zushan:episode-22:unknown"),
                probe_for(CLAIM_IDS[1]),
            ),
            "unknown claim",
        ),
        (
            lambda: (
                probe_for(CLAIM_IDS[0], source_id="media:douyin:zushan:other"),
                probe_for(CLAIM_IDS[1]),
            ),
            "source_id",
        ),
        (lambda: episode_22_probes()[:1], "coverage"),
    ],
)
def test_invalid_probe_joins_fail_closed(probes, error: str) -> None:
    """Catches a partial or untrustworthy probe join producing observations."""
    with pytest.raises(ValueError, match=error):
        compare_external_audit(
            audit_bundle=load_episode_22_audit(), local_probes=probes()
        )


def test_duplicate_probe_ids_across_distinct_claims_fail_closed() -> None:
    """Catches run-wide probe identity collisions hidden by distinct claim IDs."""
    first = probe_for(CLAIM_IDS[0])
    probes = (first, probe_for(CLAIM_IDS[1], probe_id=first.probe_id))

    with pytest.raises(ValueError, match="duplicate probe_id"):
        compare_external_audit(
            audit_bundle=load_episode_22_audit(), local_probes=probes
        )


def test_reordered_probes_produce_identical_canonical_observations() -> None:
    """Catches output ordering or IDs that depend on caller probe ordering."""
    observations = compare_external_audit(
        audit_bundle=load_episode_22_audit(), local_probes=episode_22_probes()
    )
    reordered_observations = compare_external_audit(
        audit_bundle=load_episode_22_audit(),
        local_probes=tuple(reversed(episode_22_probes())),
    )

    assert [item.model_dump(mode="json") for item in observations] == [
        item.model_dump(mode="json") for item in reordered_observations
    ]


def test_defensive_validation_rejects_an_in_memory_probe_mutation() -> None:
    """Catches trusting a caller-mutated frozen model without revalidation."""
    probes = list(episode_22_probes())
    object.__setattr__(probes[0], "source_id", "media:douyin:zushan:other")

    with pytest.raises(ValueError, match="source_id"):
        compare_external_audit(
            audit_bundle=load_episode_22_audit(), local_probes=probes
        )
