from __future__ import annotations

from kb_text_core import (
    canonical_source_locator,
    dedupe_kaiyuan_passages,
    parse_kaiyuan_passages,
)


def _volume_text() -> str:
    return (
        "# 唐開元占經 卷31\n\n"
        "　熒惑占二\n"
        "　　熒惑犯東方七宿\n"
        "　　　熒惑犯心五\n"
        "<pb:KR3g0018_WYG_031-17a>\n"
        "石氏曰熒惑守心，天下兵起。\n\n"
        "甘氏曰熒 惑 守 心，有急兵。\n"
        "<pb:KR3g0018_WYG_031-17b>\n"
        "海中占曰熒惑守心，大人憂。\n"
    )


def test_parse_kaiyuan_passages_preserves_page_heading_offsets_and_hashes():
    text = _volume_text()
    passages = parse_kaiyuan_passages(
        text,
        source_path="古籍/唐開元占經/分卷/KR3g0018_031.md",
        card_type="fenjuan",
    )

    assert len(passages) == 3
    first = passages[0]
    assert first.kb_book_id == "kaiyuan_zhanjing"
    assert first.source_locator == "KR3g0018_031"
    assert first.source_volume == "卷31"
    assert first.page_marker == "KR3g0018_WYG_031-17a"
    assert first.heading_path == [
        "唐開元占經 卷31",
        "熒惑占二",
        "熒惑犯東方七宿",
        "熒惑犯心五",
    ]
    assert first.paragraph_index == 0
    assert first.raw_text == "石氏曰熒惑守心，天下兵起。"
    assert text[first.raw_start:first.raw_end] == first.raw_text
    assert first.normalized_text == "石氏曰荧惑守心，天下兵起。"
    assert first.raw_content_hash.startswith("sha256:")
    assert first.normalized_content_hash.startswith("sha256:")

    second = passages[1]
    assert second.paragraph_index == 1
    assert second.page_marker == first.page_marker
    assert second.raw_text == "甘氏曰熒 惑 守 心，有急兵。"

    third = passages[2]
    assert third.paragraph_index == 2
    assert third.page_marker == "KR3g0018_WYG_031-17b"


def test_fulltext_page_marker_uses_same_canonical_volume_locator():
    marker = "KR3g0018_WYG_031-17a"
    assert canonical_source_locator(
        "古籍/唐開元占經/唐開元占經-全文合併版.md",
        marker,
    ) == "KR3g0018_031"

    passages = parse_kaiyuan_passages(
        _volume_text(),
        source_path="古籍/唐開元占經/唐開元占經-全文合併版.md",
        card_type="fulltext",
    )
    assert passages[0].source_locator == "KR3g0018_031"


def test_dedupe_prefers_fenjuan_and_records_fulltext_provenance():
    text = _volume_text()
    fenjuan = parse_kaiyuan_passages(
        text,
        source_path="古籍/唐開元占經/分卷/KR3g0018_031.md",
        card_type="fenjuan",
    )
    fulltext = parse_kaiyuan_passages(
        text,
        source_path="古籍/唐開元占經/唐開元占經-全文合併版.md",
        card_type="fulltext",
    )

    deduped = dedupe_kaiyuan_passages(fulltext + fenjuan)

    assert len(deduped) == len(fenjuan)
    assert all(passage.card_type == "fenjuan" for passage in deduped)
    assert deduped[0].duplicate_sources == (
        "古籍/唐開元占經/唐開元占經-全文合併版.md",
    )


def test_normalized_hash_is_stable_across_whitespace_but_raw_hash_changes():
    compact = parse_kaiyuan_passages(
        "<pb:KR3g0018_WYG_031-1a>\n熒惑守心。",
        source_path="分卷/KR3g0018_031.md",
        card_type="fenjuan",
    )[0]
    spaced = parse_kaiyuan_passages(
        "<pb:KR3g0018_WYG_031-1a>\n熒 惑 守 心。",
        source_path="分卷/KR3g0018_031.md",
        card_type="fenjuan",
    )[0]

    assert compact.normalized_content_hash == spaced.normalized_content_hash
    assert compact.raw_content_hash != spaced.raw_content_hash
