from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.video_pipeline.evidence_bundle import canonical_evidence_bundle_bytes
from src.video_pipeline.rule_assessment import build_rule_assessment_result
from src.video_pipeline.contracts import AstronomyEventV1, RuleAssessmentV1


APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parents[1]
FIXTURE_ROOT = WORKSPACE_ROOT / "tests" / "fixtures" / "evidence" / "v1"
REGRESSION_ROOT = (
    WORKSPACE_ROOT
    / "tests"
    / "fixtures"
    / "video-package"
    / "v1"
    / "evidence-rich-regression"
)


def canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def test_evidence_fixture_manifest_is_canonical_and_hash_bound() -> None:
    manifest_path = FIXTURE_ROOT / "manifest.json"
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)

    assert raw == canonical_json_bytes(manifest)
    assert manifest["schema_version"] == "evidence-fixture-manifest/v1"
    assert {item["fixture_id"] for item in manifest["fixtures"]} == {
        "evidence-rich-assessment-v1",
        "july-21-blocked-classical-v1",
    }
    for item in manifest["files"]:
        path = FIXTURE_ROOT / item["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_evidence_rich_regression_matches_committed_public_outputs() -> None:
    event = AstronomyEventV1.model_validate_json(
        (FIXTURE_ROOT / "evidence-rich-event.json").read_text(encoding="utf-8")
    )
    rules = json.loads(
        (FIXTURE_ROOT / "evidence-rich-rules.json").read_text(encoding="utf-8")
    )
    kb_root = FIXTURE_ROOT / "kb-root"

    result = build_rule_assessment_result(
        event=event,
        rules=rules,
        rule_set_version="rules:evidence-rich-v1",
        kb_root=kb_root,
    )
    expected_assessment = RuleAssessmentV1.model_validate_json(
        (REGRESSION_ROOT / "rule-assessment.json").read_text(encoding="utf-8")
    )
    expected_bundle = json.loads(
        (REGRESSION_ROOT / "evidence-bundle.json").read_text(encoding="utf-8")
    )

    assert result.assessment == expected_assessment
    assert result.evidence_bundle.model_dump(mode="json") == expected_bundle
    assert result.assessment.narration_eligibility == "eligible"
    assert result.evidence_bundle.entries[0].narration_allowed is True
    assert canonical_evidence_bundle_bytes(result.evidence_bundle) == (
        REGRESSION_ROOT / "evidence-bundle.json"
    ).read_bytes()


def test_july_21_fixture_remains_blocked_for_classical_narration() -> None:
    event = AstronomyEventV1.model_validate_json(
        (FIXTURE_ROOT / "july-21-event.json").read_text(encoding="utf-8")
    )

    result = build_rule_assessment_result(
        event=event,
        rules=[],
        rule_set_version="rules:empty-v1",
        kb_root=FIXTURE_ROOT / "kb-root",
    )

    assert result.assessment.match_status == "not_matched"
    assert result.assessment.recommended_rule_id is None
    assert result.assessment.provisional_rule_id is None
    assert result.assessment.narration_eligibility == "blocked"
    assert result.assessment.evidence_references == []
    assert result.evidence_bundle.entries == []
    assert "no_matching_rule" in result.assessment.uncertainty_reasons
