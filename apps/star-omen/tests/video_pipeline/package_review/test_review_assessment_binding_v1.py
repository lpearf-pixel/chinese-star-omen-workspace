from __future__ import annotations

from src.video_pipeline.review import expected_review_artifact_hashes
from tests.video_pipeline.package_review.helpers import july_editorial_and_script


def test_classical_review_hash_binds_rule_assessment_and_evidence_bundle() -> None:
    event, result, editorial, script = july_editorial_and_script()
    original = expected_review_artifact_hashes(
        astronomy_event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        editorial=editorial,
        stellarium_script=script,
    )
    changed_assessment = result.assessment.model_copy(
        update={"uncertainty_reasons": ["review-visible-content-change"]}
    )
    changed = expected_review_artifact_hashes(
        astronomy_event=event,
        assessment=changed_assessment,
        evidence_bundle=result.evidence_bundle,
        editorial=editorial,
        stellarium_script=script,
    )

    assert original["classical_evidence"] != changed["classical_evidence"]
    assert original["astronomy"] == changed["astronomy"]
    assert original["editorial"] == changed["editorial"]
    assert original["render"] == changed["render"]
