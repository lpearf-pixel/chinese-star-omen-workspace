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
