from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.research import build_case_report, build_research_index, validate_research_data

APP_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = APP_ROOT / "data/processed/corpus/sample_rules.json"
FIXTURE_ROOT = APP_ROOT / "data/research"


def _copy_research(tmp_path: Path) -> Path:
    root = tmp_path / "research"
    shutil.copytree(FIXTURE_ROOT, root, ignore=shutil.ignore_patterns("case_reports", "indexes"))
    (root / "case_reports").mkdir(parents=True, exist_ok=True)
    (root / "indexes").mkdir(parents=True, exist_ok=True)
    return root


def test_validate_research_data_valid_fixture(tmp_path):
    root = _copy_research(tmp_path)

    out = validate_research_data(root, RULES_PATH)

    assert out["ok"] is True
    assert out["celestial_events_count"] == 1
    assert out["historical_events_count"] == 1
    assert out["correlations_count"] == 1


def test_validate_research_data_missing_celestial_event(tmp_path):
    root = _copy_research(tmp_path)
    corr = root / "correlations/corr_mars_xin_leadership_change_001.json"
    data = json.loads(corr.read_text(encoding="utf-8"))
    data["celestial_event_id"] = "missing_celestial"
    corr.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    out = validate_research_data(root, RULES_PATH)

    assert out["ok"] is False
    assert any("missing celestial_event_id" in err for err in out["errors"])


def test_validate_research_data_missing_historical_event(tmp_path):
    root = _copy_research(tmp_path)
    corr = root / "correlations/corr_mars_xin_leadership_change_001.json"
    data = json.loads(corr.read_text(encoding="utf-8"))
    data["historical_event_id"] = "missing_historical"
    corr.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    out = validate_research_data(root, RULES_PATH)

    assert out["ok"] is False
    assert any("missing historical_event_id" in err for err in out["errors"])


def test_validate_research_data_missing_rule(tmp_path):
    root = _copy_research(tmp_path)
    corr = root / "correlations/corr_mars_xin_leadership_change_001.json"
    data = json.loads(corr.read_text(encoding="utf-8"))
    data["matched_rule_ids"] = ["missing_rule"]
    corr.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    out = validate_research_data(root, RULES_PATH)

    assert out["ok"] is False
    assert any("matched_rule_id 'missing_rule'" in err for err in out["errors"])


def test_generate_case_report_writes_markdown_and_json(tmp_path):
    root = _copy_research(tmp_path)
    out_dir = root / "case_reports"

    out = build_case_report(
        correlation_id="corr_mars_xin_leadership_change_001",
        research_root=root,
        rules_path=RULES_PATH,
        out_dir=out_dir,
    )

    md = Path(out["report_path"])
    sidecar = Path(out["json_report_path"])
    assert md.exists()
    assert sidecar.exists()
    text = md.read_text(encoding="utf-8")
    assert "天象事件摘要" in text
    assert "历史事件摘要" in text
    assert "evidence_status" in text
    assert "confidence" in text
    assert "限制与待补证据" in text
    assert "不可作为最终事实证据" in text


def test_build_research_index(tmp_path):
    root = _copy_research(tmp_path)
    build_case_report(correlation_id="corr_mars_xin_leadership_change_001", research_root=root, rules_path=RULES_PATH, out_dir=root / "case_reports")

    out = build_research_index(root)

    index_path = root / "indexes/case_index.json"
    assert index_path.exists()
    assert out["items"][0]["correlation_id"] == "corr_mars_xin_leadership_change_001"
    assert out["items"][0]["evidence_status"] == "candidate_only"
    assert out["items"][0]["report_path"].endswith("corr_mars_xin_leadership_change_001.md")


def test_validate_research_data_detects_id_filename_mismatch(tmp_path):
    root = _copy_research(tmp_path)
    hist = root / "historical_events/hist_sample_leadership_change_001.json"
    data = json.loads(hist.read_text(encoding="utf-8"))
    data["id"] = "different_id"
    hist.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    out = validate_research_data(root, RULES_PATH)

    assert out["ok"] is False
    assert any("must match filename stem" in err for err in out["errors"])


def test_validate_research_data_rejects_bad_day_date_and_bad_source_ref(tmp_path):
    root = _copy_research(tmp_path)
    hist = root / "historical_events/hist_sample_leadership_change_001.json"
    data = json.loads(hist.read_text(encoding="utf-8"))
    data["date_start"] = "not-a-date"
    data["source_refs"] = [{"note": "missing title and citation"}]
    hist.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    out = validate_research_data(root, RULES_PATH)

    assert out["ok"] is False
    assert any("date_start" in err and "not parseable" in err for err in out["errors"])
    assert any("source_refs[0]" in err for err in out["errors"])


def test_research_cli_commands_are_callable(tmp_path):
    import subprocess
    import sys

    root = _copy_research(tmp_path)
    out_dir = root / "case_reports"
    env = None

    validate_cmd = [
        sys.executable,
        "-m",
        "src.cli",
        "validate-research-data",
        "--research-root",
        str(root),
        "--rules-path",
        str(RULES_PATH),
    ]
    generate_cmd = [
        sys.executable,
        "-m",
        "src.cli",
        "generate-case-report",
        "--correlation-id",
        "corr_mars_xin_leadership_change_001",
        "--research-root",
        str(root),
        "--rules-path",
        str(RULES_PATH),
        "--out-dir",
        str(out_dir),
    ]
    index_cmd = [sys.executable, "-m", "src.cli", "build-research-index", "--research-root", str(root)]

    for cmd in [validate_cmd, generate_cmd, index_cmd]:
        completed = subprocess.run(cmd, cwd=APP_ROOT, env=env, text=True, capture_output=True, check=True)
        assert completed.stdout

    assert (out_dir / "corr_mars_xin_leadership_change_001.md").exists()
    assert (root / "indexes/case_index.json").exists()


def test_computed_evidence_status_does_not_use_rule_ids_only():
    from src.research import _computed_evidence_status

    assert _computed_evidence_status({"matched_rule_ids": ["rule_x"], "candidate_only": False, "primary_evidence_found": False, "evidence_summary": {}}) == "missing"
    assert _computed_evidence_status({"primary_evidence_found": True, "candidate_only": False}) == "primary_citable"
    assert _computed_evidence_status({"primary_evidence_found": False, "candidate_only": True, "evidence_summary": {}}) == "candidate_only"
    assert _computed_evidence_status({"primary_evidence_found": False, "candidate_only": False, "evidence_summary": {"status": "candidate_only"}}) == "candidate_only"
