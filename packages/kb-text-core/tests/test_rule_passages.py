from dataclasses import replace

from kb_text_core import parse_kaiyuan_passages
from kb_text_core.rule_passages import (
    build_passage_records,
    compare_passage_records,
)


TEXT = """# 五星占

<pb:KR3g0018_WYG_031-17a>

荧惑守心，主君忧。
"""


def passages(card_type: str, source_path: str):
    return parse_kaiyuan_passages(
        TEXT,
        source_path=source_path,
        card_type=card_type,
    )


def test_rule_passage_records_prefer_split_and_preserve_duplicate_source() -> None:
    fulltext = passages("fulltext", "唐開元占經-全文合併版.md")
    split = passages("fenjuan", "分卷/KR3g0018_031.md")

    records, ambiguities = build_passage_records(fulltext + split)

    assert ambiguities == ()
    assert len(records) == 1
    assert records[0].card_type == "fenjuan"
    assert records[0].duplicate_sources == ("唐開元占經-全文合併版.md",)
    assert records[0].passage_id.startswith("passage:sha256:")


def test_same_anchor_with_different_content_remains_ambiguous() -> None:
    first = passages("fenjuan", "a/KR3g0018_031.md")[0]
    second = replace(
        first,
        source_path="b/KR3g0018_031.md",
        raw_text="荧惑守心，兵起。",
        normalized_text="荧惑守心兵起",
        raw_content_hash="sha256:" + "a" * 64,
        normalized_content_hash="sha256:" + "b" * 64,
    )

    records, ambiguities = build_passage_records([second, first])

    assert len(records) == 2
    assert len(ambiguities) == 1
    assert set(ambiguities[0].passage_ids) == {item.passage_id for item in records}


def test_source_change_report_is_deterministic_and_explicit() -> None:
    original, _ = build_passage_records(passages("fenjuan", "分卷/KR3g0018_031.md"))
    changed_passage = replace(
        passages("fenjuan", "分卷/KR3g0018_031.md")[0],
        raw_text="荧惑守心，兵起。",
        normalized_text="荧惑守心兵起",
        raw_content_hash="sha256:" + "c" * 64,
        normalized_content_hash="sha256:" + "d" * 64,
    )
    changed, _ = build_passage_records([changed_passage])

    report = compare_passage_records(original, changed)

    assert report.status == "source_changed"
    assert len(report.changed) == 1
    assert report.changed[0].previous_passage_id == original[0].passage_id
    assert report.changed[0].current_passage_id == changed[0].passage_id
    assert report.invalidated_passage_ids == (original[0].passage_id,)


def test_added_or_removed_anchor_is_not_mislabeled_ambiguous() -> None:
    original, _ = build_passage_records(passages("fenjuan", "分卷/KR3g0018_031.md"))

    added = compare_passage_records((), original)
    removed = compare_passage_records(original, ())

    assert added.added_passage_ids == (original[0].passage_id,)
    assert removed.removed_passage_ids == (original[0].passage_id,)
    assert added.ambiguous_anchors == ()
    assert removed.ambiguous_anchors == ()
