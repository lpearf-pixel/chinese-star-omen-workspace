from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.video_pipeline.review import (
    ReviewRecordV1,
    build_review_bundle,
    evaluate_review_gate,
    expected_review_artifact_hashes,
)
from tests.video_pipeline.package_review.helpers import july_editorial_and_script


DIMENSIONS = ("astronomy", "classical_evidence", "editorial", "render")


def approved_records(event, evidence_bundle, editorial, script) -> list[ReviewRecordV1]:
    hashes = expected_review_artifact_hashes(
        astronomy_event=event,
        evidence_bundle=evidence_bundle,
        editorial=editorial,
        stellarium_script=script,
    )
    return [
        ReviewRecordV1(
            dimension=dimension,
            reviewer_role=f"reviewer:{dimension}",
            decision="approved",
            reviewed_at=datetime(2026, 7, 30, 0, 0, tzinfo=timezone.utc),
            reason="reviewed against the frozen B9 boundary",
            artifact_sha256=hashes[dimension],
        )
        for dimension in DIMENSIONS
    ]


def test_four_independent_approvals_make_july_package_previewable() -> None:
    event, result, editorial, script = july_editorial_and_script()
    reviews = build_review_bundle(
        package_id=editorial.video_package.package_id,
        records=approved_records(event, result.evidence_bundle, editorial, script),
    )

    gate = evaluate_review_gate(
        astronomy_event=event,
        editorial=editorial,
        evidence_bundle=result.evidence_bundle,
        stellarium_script=script,
        reviews=reviews,
    )

    assert gate.status == "previewable"
    assert gate.classical_publishable is False
    assert gate.missing_dimensions == []
    assert gate.blocking_reasons == []


def test_review_bundle_requires_exactly_one_record_per_dimension() -> None:
    event, result, editorial, script = july_editorial_and_script()
    records = approved_records(event, result.evidence_bundle, editorial, script)

    with pytest.raises((ValidationError, ValueError), match="dimension|review"):
        build_review_bundle(
            package_id=editorial.video_package.package_id,
            records=records[:-1],
        )

    with pytest.raises((ValidationError, ValueError), match="dimension|review"):
        build_review_bundle(
            package_id=editorial.video_package.package_id,
            records=[*records, records[0]],
        )


def test_rejected_or_tampered_review_blocks_package() -> None:
    event, result, editorial, script = july_editorial_and_script()
    records = approved_records(event, result.evidence_bundle, editorial, script)
    records[2] = records[2].model_copy(
        update={"decision": "rejected", "reason": "editorial claim needs revision"}
    )
    reviews = build_review_bundle(
        package_id=editorial.video_package.package_id,
        records=records,
    )

    gate = evaluate_review_gate(
        astronomy_event=event,
        editorial=editorial,
        evidence_bundle=result.evidence_bundle,
        stellarium_script=script,
        reviews=reviews,
    )
    assert gate.status == "blocked"
    assert "editorial" in " ".join(gate.blocking_reasons)

    tampered = reviews.model_copy(
        update={
            "records": [
                reviews.records[0].model_copy(update={"artifact_sha256": "0" * 64}),
                *reviews.records[1:],
            ]
        }
    )
    with pytest.raises((ValidationError, ValueError), match="hash|artifact|review"):
        evaluate_review_gate(
            astronomy_event=event,
            editorial=editorial,
            evidence_bundle=result.evidence_bundle,
            stellarium_script=script,
            reviews=tampered,
        )
