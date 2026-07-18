import json
from pathlib import Path

import pytest

from src.rule_engine.rule_evidence_migration import (
    apply_rule_evidence_migration,
    plan_rule_evidence_migration,
)


def _source(root: Path, name: str, page: str, text: str) -> Path:
    path = root / "古籍" / "唐開元占經" / "分卷" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# 唐開元占經\n\n## 熒惑占\n<pb:{page}>\n{text}\n", encoding="utf-8")
    return path


def _rule(rule_id: str, evidence=None):
    value = {"id": rule_id, "trigger": {"body": "mars", "event_type": "guarding"}}
    if evidence is not None:
        value["evidence"] = evidence
    return value


def test_unique_exact_primary_match_produces_revalidated_citable_proposal(tmp_path):
    root = tmp_path / "kb"
    source = _source(root, "KR3g0018_031.md", "KR3g0018_WYG_031-17a", "石氏曰熒惑守心。")
    before = source.read_bytes()
    rules = [_rule("mars-xin", {"card_type": "fenjuan", "quote": "熒惑守心"})]

    plan = plan_rule_evidence_migration(rules, kb_root=root)

    assert plan["status_counts"] == {"migratable": 1}
    detail = plan["details"][0]
    assert detail["status"] == "migratable"
    assert detail["match_type"] == "exact_raw"
    assert detail["validation_status"] == "citable"
    after = detail["after"]
    assert after["page_marker"] == "KR3g0018_WYG_031-17a"
    assert after["paragraph_index"] == 0
    assert after["source_locator"]
    assert after["heading_path"] == ["唐開元占經", "熒惑占"]
    assert after["raw_content_hash"].startswith("sha256:")
    assert after["normalized_content_hash"].startswith("sha256:")
    assert source.read_bytes() == before


def test_ambiguous_exact_match_never_produces_after(tmp_path):
    root = tmp_path / "kb"
    _source(root, "KR3g0018_031.md", "KR3g0018_WYG_031-17a", "熒惑守心。")
    _source(root, "KR3g0018_032.md", "KR3g0018_WYG_032-1a", "又曰熒惑守心。")

    plan = plan_rule_evidence_migration(
        [_rule("ambiguous", {"card_type": "fenjuan", "quote": "熒惑守心"})],
        kb_root=root,
    )

    assert plan["details"][0]["status"] == "ambiguous"
    assert plan["details"][0]["after"] is None
    assert len(plan["details"][0]["candidates"]) == 2


def test_missing_and_non_primary_evidence_remain_non_migratable(tmp_path):
    root = tmp_path / "kb"
    _source(root, "KR3g0018_031.md", "KR3g0018_WYG_031-17a", "熒惑守心。")
    rules = [
        _rule("missing"),
        _rule("term", {"card_type": "term_card", "quote": "熒惑守心"}),
    ]

    plan = plan_rule_evidence_migration(rules, kb_root=root)

    assert [row["status"] for row in plan["details"]] == [
        "missing_evidence",
        "candidate_only",
    ]
    assert all(row["after"] is None for row in plan["details"])


def test_apply_writes_separate_atomic_output_and_preserves_input(tmp_path):
    root = tmp_path / "kb"
    source = _source(root, "KR3g0018_031.md", "KR3g0018_WYG_031-17a", "熒惑守心。")
    rules_path = tmp_path / "rules.json"
    rules = [_rule("mars-xin", {"card_type": "fenjuan", "quote": "熒惑守心"})]
    rules_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")
    original_rules = rules_path.read_bytes()
    original_source = source.read_bytes()
    output = tmp_path / "migrated.json"

    plan = plan_rule_evidence_migration(rules, kb_root=root)
    result = apply_rule_evidence_migration(
        rules=rules,
        plan=plan,
        input_path=rules_path,
        output_path=output,
        kb_root=root,
    )

    migrated = json.loads(output.read_text(encoding="utf-8"))
    assert result["applied"] is True
    assert migrated[0]["evidence"]["page_marker"] == "KR3g0018_WYG_031-17a"
    assert rules_path.read_bytes() == original_rules
    assert source.read_bytes() == original_source
    with pytest.raises(ValueError, match="output path must differ from input path"):
        apply_rule_evidence_migration(
            rules=rules,
            plan=plan,
            input_path=rules_path,
            output_path=rules_path,
            kb_root=root,
        )


def test_apply_rejects_tampered_plan_and_raw_corpus_output(tmp_path):
    root = tmp_path / "kb"
    source = _source(root, "KR3g0018_031.md", "KR3g0018_WYG_031-17a", "熒惑守心。")
    rules_path = tmp_path / "rules.json"
    rules = [_rule("mars-xin", {"card_type": "fenjuan", "quote": "熒惑守心"})]
    rules_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")
    plan = plan_rule_evidence_migration(rules, kb_root=root)
    plan["details"][0]["after"]["page_marker"] = "tampered"

    with pytest.raises(ValueError, match="planned evidence is not currently citable"):
        apply_rule_evidence_migration(
            rules=rules,
            plan=plan,
            input_path=rules_path,
            output_path=tmp_path / "out.json",
            kb_root=root,
        )
    clean = plan_rule_evidence_migration(rules, kb_root=root)
    with pytest.raises(ValueError, match="output path must be outside kb_root"):
        apply_rule_evidence_migration(
            rules=rules,
            plan=clean,
            input_path=rules_path,
            output_path=source,
            kb_root=root,
        )


def test_malformed_evidence_is_invalid_and_missing_root_fails(tmp_path):
    root = tmp_path / "kb"
    _source(root, "KR3g0018_031.md", "KR3g0018_WYG_031-17a", "熒惑守心。")
    plan = plan_rule_evidence_migration(
        [{"id": "bad", "evidence": []}],
        kb_root=root,
    )
    assert plan["details"][0]["status"] == "invalid_rule"
    with pytest.raises(ValueError, match="kb_root must be an existing directory"):
        plan_rule_evidence_migration([], kb_root=tmp_path / "missing")
