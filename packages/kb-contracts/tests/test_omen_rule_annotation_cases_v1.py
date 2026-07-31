from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CASES = ROOT / "tests/fixtures/rules/v2/annotation-cases"
MANIFEST = CASES / "manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_annotation_case_manifest_freezes_exact_assets() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "annotation-case-manifest/v1"
    assert manifest["guide_version"] == "kaiyuan-rule-annotation/v1"
    assert manifest["status"] == "frozen"
    guide = ROOT / manifest["guide_path"]
    assert guide.is_file() and not guide.is_symlink()
    assert sha256(guide) == manifest["guide_sha256"]

    expected = [item["path"] for item in manifest["cases"]]
    actual = sorted(path.name for path in CASES.glob("*.json") if path != MANIFEST)
    assert expected == actual
    assert len(expected) == 6

    for item in manifest["cases"]:
        path = CASES / item["path"]
        assert path.is_file() and not path.is_symlink()
        assert sha256(path) == item["sha256"]


def test_annotation_cases_cover_required_structural_decisions() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = [
        json.loads((CASES / item["path"]).read_text(encoding="utf-8"))
        for item in manifest["cases"]
    ]

    assert all(case["guide_version"] == manifest["guide_version"] for case in cases)
    assert all(case["review_status"] == "contract_frozen" for case in cases)
    assert len({case["case_id"] for case in cases}) == len(cases)
    assert {
        case["decision"] for case in cases
    } >= {
        "one_passage_one_rule",
        "one_passage_multiple_rules",
        "multiple_passages_one_rule",
        "resolve_subject_from_heading",
        "retain_without_formal_candidate",
    }
    assert any(case["expected_candidate_count"] > 1 for case in cases)
    assert any(len(group) > 1 for case in cases for group in case["expected_groups"])
    assert any(case.get("eligibility") == "needs_review" for case in cases)
    assert any(case["computability"] == "not_computable" for case in cases)


def test_frozen_cases_never_claim_missing_text_as_formal_rule() -> None:
    ambiguous = json.loads(
        (CASES / "05-variant-ambiguous.json").read_text(encoding="utf-8")
    )

    assert ambiguous["expected_candidate_count"] == 0
    assert ambiguous["expected_groups"] == []
    assert ambiguous["eligibility"] == "needs_review"
