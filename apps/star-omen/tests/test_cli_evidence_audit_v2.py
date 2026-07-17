from __future__ import annotations

import json
from pathlib import Path

import pytest
from kb_text_core import parse_kaiyuan_passages
from typer.testing import CliRunner

from src.cli import app, resolve_evidence_impl
from src.rule_engine.minimal_matcher import match_event_to_rules


PAGE = "KR3g0018_WYG_031-17a"
RAW = "石氏曰熒惑守心，天下兵起。"


def _fixture(root: Path) -> dict:
    path = root / "古籍" / "唐開元占經" / "分卷" / "KR3g0018_031.md"
    path.parent.mkdir(parents=True)
    text = (
        "# 唐開元占經 卷31\n\n"
        "　熒惑占二\n"
        "　　　熒惑犯心五\n"
        f"<pb:{PAGE}>\n{RAW}\n"
    )
    path.write_text(text, encoding="utf-8")
    passage = parse_kaiyuan_passages(
        text,
        source_path=str(path),
        card_type="fenjuan",
    )[0]
    return {
        "kb_book_id": "kaiyuan_zhanjing",
        "card_type": "fenjuan",
        "relative_path": "古籍/唐開元占經/分卷/KR3g0018_031.md",
        "source_locator": "KR3g0018_031",
        "page_marker": PAGE,
        "heading_path": passage.heading_path,
        "paragraph_index": passage.paragraph_index,
        "anchor_text": RAW,
        "content_hash": passage.raw_content_hash,
    }


def test_resolve_evidence_strict_reports_precise_validation_status(tmp_path: Path):
    evidence = _fixture(tmp_path)
    evidence["content_hash"] = "sha256:" + "0" * 64
    rule_path = tmp_path / "rule.json"
    rule_path.write_text(
        json.dumps({"id": "r-hash", "evidence": evidence}, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="hash_mismatch"):
        resolve_evidence_impl(rule_path, kb_root=tmp_path, strict=True)


def test_audit_rules_counts_every_validation_status_and_includes_trace(tmp_path: Path):
    citable = _fixture(tmp_path)
    bad_hash = dict(citable)
    bad_hash["content_hash"] = "sha256:" + "f" * 64
    rules = [
        {"id": "r-citable", "evidence": citable},
        {"id": "r-structured", "evidence": {"card_type": "term_card"}},
        {"id": "r-hash", "evidence": bad_hash},
        {"id": "r-missing"},
    ]
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "audit-rules",
            "--rules-path",
            str(rules_path),
            "--kb-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    body = json.loads(result.stdout)
    assert body["total_rules"] == 4
    assert body["citable"] == 1
    assert body["candidate_only"] == 1
    assert body["missing_evidence"] == 1
    assert body["status_counts"] == {
        "candidate_only": 1,
        "citable": 1,
        "hash_mismatch": 1,
        "missing_evidence": 1,
    }
    by_id = {row["rule_id"]: row for row in body["details"]}
    assert by_id["r-hash"]["status"] == "hash_mismatch"
    assert by_id["r-hash"]["candidate_reason"] == "content_hash_does_not_match_anchor_or_passage"
    assert by_id["r-hash"]["trace"]["validation_version"] == "citable-evidence/v2"


def test_rule_matcher_surfaces_mismatch_and_never_promotes_it_to_primary(tmp_path: Path):
    evidence = _fixture(tmp_path)
    evidence["page_marker"] = "KR3g0018_WYG_031-99b"
    rules = [
        {
            "id": "r-page",
            "trigger": {
                "body": "mars",
                "event_type": "conjunction",
                "target": "heart",
            },
            "evidence": evidence,
            "rule_priority": 1,
        }
    ]
    event = {
        "id": "event-1",
        "body": "mars",
        "event_type": "conjunction",
        "target_asterism": "heart",
        "visibility": {"is_visible": True},
    }

    result = match_event_to_rules(event=event, rules=rules, kb_root=tmp_path)

    assert result["match_status"] == "candidate_only"
    assert result["primary_evidence_found"] is False
    assert result["candidate_only"] is True
    assert result["evidence_summary"]["status"] == "page_mismatch"
    assert result["evidence_summary"]["candidate_reason"] == "page_marker_not_found_in_source_locator"
    assert result["evidence_summary"]["validation_version"] == "citable-evidence/v2"
