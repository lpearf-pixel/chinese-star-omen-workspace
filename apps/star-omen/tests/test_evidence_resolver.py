from pathlib import Path

import src.connectors.evidence_resolver as resolver_module
from src.connectors.evidence_resolver import EvidenceResolverContext, resolve_evidence


def test_resolve_evidence_marks_candidate_only_for_non_primary(tmp_path: Path):
    evidence = {"card_type": "term_card", "relative_path": "a.md"}
    out = resolve_evidence(evidence, tmp_path)
    assert out["status"] == "candidate_only"
    assert out["final_citable"] is False
    assert out["ingest_source"] == "obsidian"
    assert out["source_type"] == "docs"


def test_primary_label_on_generic_file_is_not_enough_for_citation(tmp_path: Path):
    file_path = tmp_path / "docs" / "x.md"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("hello", encoding="utf-8")
    evidence = {
        "card_type": "fenjuan",
        "relative_path": "docs/x.md",
        "locator": "卷十二",
        "quote": "荧惑守心",
    }
    out = resolve_evidence(evidence, tmp_path)
    assert out["status"] == "candidate_only"
    assert out["candidate_reason"] in {
        "missing_kb_book_id",
        "unrecognized_primary_source_path",
    }
    assert out["final_citable"] is False
    assert out["path_exists"] is True
    assert out["volume"] == "卷十二"
    assert out["section"] == "卷十二"
    assert out["source_locator"] == "卷十二"
    assert out["anchor_text"] == "荧惑守心"


def test_resolve_evidence_includes_anchor_fields():
    out = resolve_evidence(
        {
            "card_type": "fenjuan",
            "relative_path": "docs/卷十二.md",
            "volume": "卷十二",
            "section": "荧惑占",
            "source_locator": "卷十二/荧惑占/第三段",
            "heading_path": ["卷十二", "荧惑占"],
            "anchor_text": "荧惑守心",
            "paragraph_index": 2,
        }
    )
    assert out["volume"] == "卷十二"
    assert out["section"] == "荧惑占"
    assert out["source_locator"] == "卷十二/荧惑占/第三段"
    assert out["heading_path"] == ["卷十二", "荧惑占"]
    assert out["anchor_text"] == "荧惑守心"
    assert out["paragraph_index"] == 2


def test_explicit_root_and_context_do_not_consult_global_settings(
    monkeypatch, tmp_path: Path
):
    def forbidden_settings():
        raise AssertionError("explicit resolver context must be self-contained")

    monkeypatch.setattr(resolver_module, "get_settings", forbidden_settings)
    out = resolve_evidence(
        {"card_type": "term_card", "relative_path": "a.md"},
        tmp_path,
        resolver_context=EvidenceResolverContext(
            source_root_label="source-snapshot",
            ingest_source_label="snapshot-ingest",
        ),
    )

    assert out["status"] == "candidate_only"
    assert out["ingest_source"] == "snapshot-ingest"
    assert out["trace"]["source_root_label"] == "source-snapshot"
