from __future__ import annotations

import sys
from pathlib import Path

INDEX_JOBS = Path(__file__).resolve().parents[1] / "index-jobs"
sys.path.insert(0, str(INDEX_JOBS))

from desired_items import collect_desired_items  # noqa: E402


def _primary_text() -> str:
    return (
        "# 唐開元占經 卷31\n"
        "　熒惑占二\n"
        "　　熒惑犯東方七宿\n"
        "　　　熒惑犯心五\n"
        "<pb:KR3g0018_WYG_031-17a>\n"
        "石氏曰熒惑守心，天下兵起。\n"
    )


def test_collect_desired_items_prefers_fenjuan_over_duplicate_fulltext(tmp_path: Path):
    sources = tmp_path / "sources"
    corpus = sources / "古籍" / "唐開元占經"
    volume = corpus / "分卷" / "KR3g0018_031.md"
    volume.parent.mkdir(parents=True)
    volume.write_text(_primary_text(), encoding="utf-8")
    fulltext = corpus / "唐開元占經-全文合併版.md"
    fulltext.write_text(_primary_text(), encoding="utf-8")

    desired = collect_desired_items(
        sources,
        generated_root=tmp_path / "generated",
        obsidian_root=None,
        chunk_size=700,
        overlap=120,
    )

    primary = [item for item in desired if item.get("card_type") == "fenjuan"]
    assert len(primary) == 1
    item = primary[0]
    assert item["source_locator"] == "KR3g0018_031"
    assert item["page_marker"] == "KR3g0018_WYG_031-17a"
    assert item["heading_path"][-1] == "熒惑犯心五"
    assert item["chunk_text"] == "石氏曰熒惑守心，天下兵起。"
    assert item["managed_by"] == "local-kb-unified/v2"
    assert item["collection_schema"] == "passage-v2"
    assert str(fulltext.resolve()) in item["duplicate_sources"]


def test_generated_pending_cards_are_excluded_but_approved_cards_are_included(tmp_path: Path):
    sources = tmp_path / "sources"
    sources.mkdir()
    generated = tmp_path / "generated" / "extract_cards" / "kaiyuan_zhanjing"
    generated.mkdir(parents=True)
    pending = generated / "pending.md"
    pending.write_text(
        "---\n"
        "kb_book_id: kaiyuan_zhanjing\n"
        "card_type: extract_card\n"
        "review_status: pending\n"
        "source_namespace: downstream_generated\n"
        "---\n\n待审候选。\n",
        encoding="utf-8",
    )
    approved = generated / "approved.md"
    approved.write_text(
        "---\n"
        "kb_book_id: kaiyuan_zhanjing\n"
        "card_type: extract_card\n"
        "review_status: approved\n"
        "source_namespace: official\n"
        "---\n\n已审证据卡。\n",
        encoding="utf-8",
    )

    desired = collect_desired_items(
        sources,
        generated_root=tmp_path / "generated",
        obsidian_root=None,
        chunk_size=700,
        overlap=120,
    )

    paths = {Path(str(item["path"])).name for item in desired}
    assert "approved.md" in paths
    assert "pending.md" not in paths
    approved_item = next(item for item in desired if Path(str(item["path"])).name == "approved.md")
    assert approved_item["managed_by"] == "local-kb-unified/v2"
    assert approved_item["kb_book_id"] == "kaiyuan_zhanjing"


def test_generic_identity_uses_relative_source_path_not_machine_absolute_path(tmp_path: Path):
    sources = tmp_path / "sources"
    doc = sources / "docs" / "note.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("A stable note.", encoding="utf-8")

    desired = collect_desired_items(
        sources,
        generated_root=tmp_path / "generated",
        obsidian_root=None,
        chunk_size=700,
        overlap=120,
    )

    assert len(desired) == 1
    assert desired[0]["relative_path"] == "docs/note.md"
    assert desired[0]["source_root_label"] == "primary"
    assert desired[0]["content_hash"].startswith("sha256:")
