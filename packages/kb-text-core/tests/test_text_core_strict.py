from pathlib import Path

from kb_text_core import (
    audit_kaiyuan_corpus,
    build_anchor_context,
    find_match_spans,
)


def test_nested_ancient_headings_are_preserved():
    text = (
        "# 唐開元占經 卷31\n\n"
        "　熒惑占二\n"
        "　　熒惑犯東方七宿\n"
        "　　　熒惑犯心五\n"
        "<pb:KR3g0018_WYG_031-17a>\n"
        "石氏曰熒惑守心。\n"
    )
    start = text.index("熒惑守心")
    context = build_anchor_context(text, start, start + len("熒惑守心"))

    assert context.heading_path == [
        "唐開元占經 卷31",
        "熒惑占二",
        "熒惑犯東方七宿",
        "熒惑犯心五",
    ]
    assert context.page_marker == "KR3g0018_WYG_031-17a"
    assert "石氏曰熒惑守心" in context.anchor_text


def test_heading_only_is_not_promoted_to_exact_primary():
    text = "# 唐開元占經 卷31\n\n　　　熒惑守心\n正文另述他事。\n"
    spans = find_match_spans(
        text,
        "荧惑守心",
        allow_loose=False,
    )

    assert spans
    assert {span.match_type for span in spans} == {"heading_only"}


def test_strict_audit_accepts_complete_121_section_fixture(tmp_path: Path):
    fulltext = tmp_path / "唐開元占經-全文合併版.md"
    volumes = tmp_path / "分卷"
    volumes.mkdir()

    sections: list[str] = []
    for number in range(121):
        if number == 0:
            heading = "# 唐開元占經 目錄/議語"
        else:
            heading = f"# 唐開元占經 卷{number}"
        marker = f"<pb:KR3g0018_WYG_{number:03d}-1a>"
        section = f"{heading}\n{marker}\n第{number}部分。\n"
        sections.append(section)
        (volumes / f"KR3g0018_{number:03d}.md").write_text(
            section,
            encoding="utf-8",
        )

    fulltext.write_text("\n".join(sections), encoding="utf-8")
    report = audit_kaiyuan_corpus(fulltext, volumes)

    assert report["ok"] is True
    assert report["section_count"] == 121
    assert report["stripped_equal_count"] == 121
    assert report["missing_sections"] == []
    assert report["missing_volume_files"] == []
    assert report["page_marker_volume_mismatches"] == []


def test_strict_audit_reports_page_volume_mismatch(tmp_path: Path):
    fulltext = tmp_path / "full.md"
    volumes = tmp_path / "分卷"
    volumes.mkdir()

    sections: list[str] = []
    for number in range(121):
        heading = (
            "# 唐開元占經 目錄/議語"
            if number == 0
            else f"# 唐開元占經 卷{number}"
        )
        marker_volume = 99 if number == 31 else number
        section = (
            f"{heading}\n"
            f"<pb:KR3g0018_WYG_{marker_volume:03d}-1a>\n"
            f"第{number}部分。\n"
        )
        sections.append(section)
        (volumes / f"KR3g0018_{number:03d}.md").write_text(
            section,
            encoding="utf-8",
        )

    fulltext.write_text("\n".join(sections), encoding="utf-8")
    report = audit_kaiyuan_corpus(fulltext, volumes)

    assert report["ok"] is False
    assert report["page_marker_volume_mismatches"] == [
        {
            "source_locator": "KR3g0018_031",
            "page_marker": "KR3g0018_WYG_099-1a",
            "expected_volume": "031",
            "actual_volume": "099",
        }
    ]
