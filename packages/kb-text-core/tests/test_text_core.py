from pathlib import Path

from kb_text_core import (
    audit_kaiyuan_corpus,
    build_anchor_context,
    cluster_match_spans,
    dedupe_primary_hits,
    find_match_spans,
    normalize_search_text,
    split_kaiyuan_fulltext,
)


def test_whitespace_and_traditional_match_preserve_raw_offset():
    text = "序  \n熒 惑 守 心，天下兵起。"
    spans = find_match_spans(text, "荧惑守心", allow_loose=False)
    assert spans
    assert spans[0].match_type == "exact_normalized"
    assert spans[0].start == text.index("熒")
    assert text[spans[0].start:spans[0].end] == "熒 惑 守 心"


def test_anchor_extracts_page_and_ancient_heading():
    text = "# 唐開元占經 卷31\n\n　　　熒惑犯心五\n<pb:KR3g0018_WYG_031-17a>\n石氏曰熒惑守心。"
    start = text.index("熒惑守心")
    context = build_anchor_context(text, start, start + 5)
    assert context.page_marker == "KR3g0018_WYG_031-17a"
    assert context.heading_path[-1] == "熒惑犯心五"
    assert "熒惑守心" in context.anchor_text


def test_cluster_groups_matches_on_same_page_and_heading():
    text = "# 唐開元占經 卷31\n　　　熒惑犯心五\n<pb:KR3g0018_WYG_031-17a>\n熒惑守心。又曰熒惑守心。"
    spans = find_match_spans(text, "荧惑守心", allow_loose=False)
    clusters = cluster_match_spans(text, spans)
    assert len(spans) == 2
    assert len(clusters) == 1
    assert len(clusters[0].spans) == 2


def test_dedupe_prefers_fenjuan_over_fulltext():
    common = {
        "kb_book_id": "kaiyuan_zhanjing",
        "page_marker": "KR3g0018_WYG_031-17a",
        "anchor_text": "石氏曰熒惑守心",
        "match_type": "exact_raw",
        "match_offset": 10,
    }
    hits = dedupe_primary_hits([
        {**common, "card_type": "fulltext", "score": 0.85, "path": "full.md"},
        {**common, "card_type": "fenjuan", "score": 1.0, "path": "KR3g0018_031.md"},
    ])
    assert len(hits) == 1
    assert hits[0]["card_type"] == "fenjuan"


def test_normalized_fenjuan_ranks_before_raw_fulltext():
    common = {
        "kb_book_id": "kaiyuan_zhanjing",
        "page_marker": "KR3g0018_WYG_031-17a",
        "anchor_text": "石氏曰熒惑守心",
        "match_offset": 10,
    }
    hits = dedupe_primary_hits([
        {**common, "match_type": "exact_raw", "card_type": "fulltext", "score": 0.85, "path": "full.md"},
        {**common, "match_type": "exact_normalized", "card_type": "fenjuan", "score": 0.95, "path": "KR3g0018_031.md"},
    ])
    assert len(hits) == 1
    assert hits[0]["card_type"] == "fenjuan"
    assert hits[0]["match_type"] == "exact_normalized"


def test_split_fulltext_recognizes_directory_and_volumes():
    text = "# 唐開元占經 目錄/議語\n目錄\n\n# 唐開元占經 卷1\n卷一\n\n# 唐開元占經 卷2\n卷二\n"
    sections = split_kaiyuan_fulltext(text)
    assert list(sections) == ["KR3g0018_000", "KR3g0018_001", "KR3g0018_002"]


def test_normalize_search_text_preserves_entities_and_normalizes_variant():
    assert normalize_search_text("熒 惑 &KR2343;") == "荧惑&KR2343;"


def test_normalize_search_text_does_not_rewrite_ambiguous_common_characters():
    assert normalize_search_text("千里臺下") == "千里台下"
    assert "裏" not in normalize_search_text("千里")


def test_audit_reports_full_volume_agreement(tmp_path: Path):
    fulltext = tmp_path / "full.md"
    volumes = tmp_path / "volumes"
    volumes.mkdir()
    fulltext.write_text(
        "# 唐開元占經 目錄/議語\n目錄\n\n# 唐開元占經 卷1\n卷一\n",
        encoding="utf-8",
    )
    (volumes / "KR3g0018_000.md").write_text("# 唐開元占經 目錄/議語\n目錄\n", encoding="utf-8")
    (volumes / "KR3g0018_001.md").write_text("# 唐開元占經 卷1\n卷一\n", encoding="utf-8")
    report = audit_kaiyuan_corpus(fulltext, volumes)
    assert report["section_count"] == 2
    assert report["different_volumes"] == []
