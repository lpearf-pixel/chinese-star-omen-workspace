from __future__ import annotations

import os
from pathlib import Path

import pytest

import src.connectors.evidence_resolver as resolver_module
import src.connectors.primary_passage_cache as cache_module
from kb_text_core import parse_kaiyuan_passages
from src.connectors.evidence_resolver import resolve_evidence
from src.connectors.kb_contract import is_citable_evidence
from src.connectors.primary_passage_cache import PrimaryPassageCache


RAW_PASSAGE = "石氏曰熒惑守心，天下兵起。"
PAGE_MARKER = "KR3g0018_WYG_031-17a"
LOCATOR = "KR3g0018_031"


def _text() -> str:
    return (
        "# 唐開元占經 卷31\n\n"
        "　熒惑占二\n"
        "　　熒惑犯東方七宿\n"
        "　　　熒惑犯心五\n"
        f"<pb:{PAGE_MARKER}>\n"
        f"{RAW_PASSAGE}\n\n"
        "甘氏曰熒惑守心，有急兵。\n"
    )


def _write_volume(root: Path) -> tuple[Path, dict]:
    path = root / "古籍" / "唐開元占經" / "分卷" / "KR3g0018_031.md"
    path.parent.mkdir(parents=True)
    text = _text()
    path.write_text(text, encoding="utf-8")
    passage = parse_kaiyuan_passages(
        text,
        source_path=str(path),
        card_type="fenjuan",
    )[0]
    evidence = {
        "kb_book_id": "kaiyuan_zhanjing",
        "card_type": "fenjuan",
        "evidence_level": "primary",
        "relative_path": "古籍/唐開元占經/分卷/KR3g0018_031.md",
        "source_locator": LOCATOR,
        "source_volume": "卷31",
        "page_marker": PAGE_MARKER,
        "heading_path": list(passage.heading_path),
        "paragraph_index": passage.paragraph_index,
        "anchor_text": RAW_PASSAGE,
        "content_hash": passage.raw_content_hash,
        "raw_content_hash": passage.raw_content_hash,
        "normalized_content_hash": passage.normalized_content_hash,
    }
    return path, evidence


def test_fully_matched_fenjuan_passage_is_citable(tmp_path: Path):
    path, evidence = _write_volume(tmp_path)

    resolved = resolve_evidence(evidence, tmp_path)

    assert resolved["status"] == "citable"
    assert resolved["final_citable"] is True
    assert resolved["resolved_path"] == str(path.resolve())
    assert resolved["source_locator"] == LOCATOR
    assert resolved["page_marker"] == PAGE_MARKER
    assert resolved["paragraph_index"] == 0
    assert resolved["anchor_text"] == RAW_PASSAGE
    assert resolved["trace"]["validation_version"] == "citable-evidence/v2"
    assert all(resolved["trace"]["checks"].values())
    assert resolved["trace"]["matched_passage"]["raw_text"] == RAW_PASSAGE
    assert is_citable_evidence(resolved) is True


def test_fulltext_marker_maps_to_same_canonical_volume_locator(tmp_path: Path):
    path = tmp_path / "古籍" / "唐開元占經" / "唐開元占經-全文合併版.md"
    path.parent.mkdir(parents=True)
    text = _text()
    path.write_text(text, encoding="utf-8")
    passage = parse_kaiyuan_passages(
        text,
        source_path=str(path),
        card_type="fulltext",
    )[0]

    resolved = resolve_evidence(
        {
            "kb_book_id": "kaiyuan_zhanjing",
            "card_type": "fulltext",
            "relative_path": "古籍/唐開元占經/唐開元占經-全文合併版.md",
            "source_locator": LOCATOR,
            "page_marker": PAGE_MARKER,
            "paragraph_index": passage.paragraph_index,
            "heading_path": passage.heading_path,
            "anchor_text": RAW_PASSAGE,
            "content_hash": passage.raw_content_hash,
        },
        tmp_path,
    )

    assert resolved["status"] == "citable"
    assert resolved["source_locator"] == LOCATOR
    assert resolved["trace"]["matched_passage"]["card_type"] == "fulltext"


def test_normalized_anchor_matches_without_rewriting_raw_source(tmp_path: Path):
    path, evidence = _write_volume(tmp_path)
    before = path.read_bytes()
    evidence["anchor_text"] = "石氏曰荧 惑 守 心，天下兵起。"
    # Anchor hashes may describe the supplied excerpt while passage hashes retain raw provenance.
    evidence.pop("content_hash")
    evidence.pop("raw_content_hash")

    resolved = resolve_evidence(evidence, tmp_path)

    assert resolved["status"] == "citable"
    assert resolved["trace"]["anchor_match_type"] == "normalized"
    assert resolved["trace"]["matched_passage"]["raw_text"] == RAW_PASSAGE
    assert path.read_bytes() == before


def test_non_primary_and_incomplete_primary_references_remain_candidate_only(tmp_path: Path):
    _write_volume(tmp_path)
    structured = resolve_evidence(
        {"card_type": "term_card", "relative_path": "cards/熒惑.md"},
        tmp_path,
    )
    assert structured["status"] == "candidate_only"
    assert structured["candidate_reason"] == "card_type_not_primary"

    incomplete = resolve_evidence(
        {
            "kb_book_id": "kaiyuan_zhanjing",
            "card_type": "fenjuan",
            "relative_path": "古籍/唐開元占經/分卷/KR3g0018_031.md",
            "source_locator": LOCATOR,
            "page_marker": PAGE_MARKER,
        },
        tmp_path,
    )
    assert incomplete["status"] == "candidate_only"
    assert incomplete["candidate_reason"] in {"missing_anchor", "missing_hash"}
    assert is_citable_evidence(incomplete) is False

    forged = {
        "card_type": "fenjuan",
        "evidence_level": "primary",
        "relative_path": "x.md",
        "status": "citable",
    }
    assert is_citable_evidence(forged) is False


@pytest.mark.parametrize(
    ("mutation", "expected_status"),
    [
        ({"kb_book_id": "other_book"}, "book_mismatch"),
        ({"card_type": "fulltext"}, "card_type_mismatch"),
        ({"source_locator": "KR3g0018_032"}, "locator_mismatch"),
        ({"page_marker": "KR3g0018_WYG_031-99b"}, "page_mismatch"),
        ({"paragraph_index": 99}, "paragraph_mismatch"),
        ({"heading_path": ["错误标题"]}, "heading_mismatch"),
        ({"anchor_text": "原文不存在"}, "anchor_mismatch"),
        ({"content_hash": "sha256:" + "0" * 64}, "hash_mismatch"),
    ],
)
def test_precise_primary_mismatch_statuses(tmp_path: Path, mutation: dict, expected_status: str):
    _path, evidence = _write_volume(tmp_path)
    evidence.update(mutation)

    resolved = resolve_evidence(evidence, tmp_path)

    assert resolved["status"] == expected_status
    assert resolved["final_citable"] is False
    assert is_citable_evidence(resolved) is False
    assert resolved["trace"]["validation_version"] == "citable-evidence/v2"


def test_missing_and_outside_root_sources_fail_closed(tmp_path: Path):
    _path, evidence = _write_volume(tmp_path)

    missing = dict(evidence)
    missing["relative_path"] = "古籍/唐開元占經/分卷/KR3g0018_099.md"
    assert resolve_evidence(missing, tmp_path)["status"] == "missing_source"

    outside_path = tmp_path.parent / "outside-KR3g0018_031.md"
    outside_path.write_text(_text(), encoding="utf-8")
    outside = dict(evidence)
    outside["relative_path"] = "../outside-KR3g0018_031.md"
    assert resolve_evidence(outside, tmp_path)["status"] == "source_outside_root"


def test_repeated_resolution_reuses_parse_but_revalidates_changed_bytes(
    monkeypatch, tmp_path: Path
):
    path, evidence = _write_volume(tmp_path)
    original_stat = path.stat()
    isolated_cache = PrimaryPassageCache()
    monkeypatch.setattr(resolver_module, "primary_passage_cache", isolated_cache)
    real_parser = cache_module.parse_kaiyuan_passages
    calls = 0

    def counting_parser(*args, **kwargs):
        nonlocal calls
        calls += 1
        return real_parser(*args, **kwargs)

    monkeypatch.setattr(cache_module, "parse_kaiyuan_passages", counting_parser)

    first = resolve_evidence(evidence, tmp_path)
    second = resolve_evidence(evidence, tmp_path)
    assert first["status"] == second["status"] == "citable"
    assert calls == 1

    changed = path.read_text(encoding="utf-8").replace("天下兵起", "天下兵止")
    path.write_text(changed, encoding="utf-8")
    os.utime(path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    assert path.stat().st_size == original_stat.st_size
    assert path.stat().st_mtime_ns == original_stat.st_mtime_ns

    invalidated = resolve_evidence(evidence, tmp_path)
    assert invalidated["status"] == "anchor_mismatch"
    assert invalidated["final_citable"] is False
    assert calls == 2

    path.unlink()
    assert resolve_evidence(evidence, tmp_path)["status"] == "missing_source"
