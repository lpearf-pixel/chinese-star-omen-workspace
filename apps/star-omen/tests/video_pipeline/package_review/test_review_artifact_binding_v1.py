from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest

from src.video_pipeline.contracts import canonical_contract_bytes
from src.video_pipeline.editorial import canonical_editorial_bytes
from src.video_pipeline.review import ReviewRecordV1, build_review_bundle, evaluate_review_gate
from tests.video_pipeline.package_review.helpers import july_editorial_and_script


DIMENSIONS = ("astronomy", "classical_evidence", "editorial", "render")


def expected_hashes(event, result, editorial, script) -> dict[str, str]:
    classical_payload = {
        "assessment": result.assessment.model_dump(mode="json", exclude_none=False),
        "evidence_bundle": result.evidence_bundle.model_dump(
            mode="json", exclude_none=False
        ),
    }
    return {
        "astronomy": hashlib.sha256(canonical_contract_bytes(event)).hexdigest(),
        "classical_evidence": hashlib.sha256(
            canonical_contract_bytes(classical_payload)
        ).hexdigest(),
        "editorial": hashlib.sha256(canonical_editorial_bytes(editorial)).hexdigest(),
        "render": script.sha256,
    }


def records_for(hashes: dict[str, str]) -> list[ReviewRecordV1]:
    return [
        ReviewRecordV1(
            dimension=dimension,
            reviewer_role=f"reviewer:{dimension}",
            decision="approved",
            reviewed_at=datetime(2026, 7, 30, 0, 0, tzinfo=timezone.utc),
            reason="independently reviewed the dimension-specific artifact",
            artifact_sha256=hashes[dimension],
        )
        for dimension in DIMENSIONS
    ]


def test_review_gate_binds_each_dimension_to_its_own_canonical_artifact() -> None:
    event, result, editorial, script = july_editorial_and_script()
    hashes = expected_hashes(event, result, editorial, script)
    reviews = build_review_bundle(
        package_id=editorial.video_package.package_id,
        records=records_for(hashes),
    )

    gate = evaluate_review_gate(
        astronomy_event=event,
        assessment=result.assessment,
        editorial=editorial,
        evidence_bundle=result.evidence_bundle,
        stellarium_script=script,
        reviews=reviews,
    )

    assert gate.status == "previewable"


def test_review_gate_rejects_script_hash_reused_for_all_dimensions() -> None:
    event, result, editorial, script = july_editorial_and_script()
    reused = {dimension: script.sha256 for dimension in DIMENSIONS}
    reviews = build_review_bundle(
        package_id=editorial.video_package.package_id,
        records=records_for(reused),
    )

    with pytest.raises((ValueError, TypeError), match="artifact|hash|astronomy"):
        evaluate_review_gate(
            astronomy_event=event,
            assessment=result.assessment,
            editorial=editorial,
            evidence_bundle=result.evidence_bundle,
            stellarium_script=script,
            reviews=reviews,
        )
