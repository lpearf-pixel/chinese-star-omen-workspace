from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from typing import Iterator

from .anchors import PAGE_MARKER_RE, heading_path_at, heading_ranges
from .models import KaiyuanPassage
from .normalization import normalize_search_text

VOLUME_PATH_RE = re.compile(r"(KR[0-9A-Za-z]+_\d{3})(?:\.md|$)")
PAGE_VOLUME_RE = re.compile(
    r"^(KR[0-9A-Za-z]+)(?:_[A-Za-z0-9]+)*_(\d{3})(?:-|$)"
)
BLANK_LINE_RE = re.compile(r"\n[ \t　]*\n")
PRIMARY_CARD_TYPES = {"fenjuan", "fulltext"}


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_source_locator(
    source_path: str,
    page_marker: str | None = None,
) -> str:
    """Map split-volume paths and fulltext page markers to one volume locator."""

    normalized = str(source_path or "").replace("\\", "/")
    path_match = VOLUME_PATH_RE.search(normalized)
    if path_match:
        return path_match.group(1)

    marker_match = PAGE_VOLUME_RE.search(str(page_marker or ""))
    if marker_match:
        return f"{marker_match.group(1)}_{marker_match.group(2)}"

    if "全文合併版" in normalized or "全文合并版" in normalized:
        return "fulltext"
    name = normalized.rsplit("/", 1)[-1]
    return re.sub(r"\.md$", "", name) or "unknown"


def source_volume_for_locator(source_locator: str) -> str | None:
    match = re.search(r"_(\d{3})(?:-|$)", source_locator)
    return f"卷{int(match.group(1))}" if match else None


def _trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _drop_leading_headings(
    text: str,
    start: int,
    end: int,
    ranges: list[tuple[int, int, str, int]],
) -> tuple[int, int]:
    changed = True
    while changed:
        changed = False
        start, end = _trim_span(text, start, end)
        for left, right, _, _ in ranges:
            if left == start and right <= end:
                start = right
                changed = True
                break
    return _trim_span(text, start, end)


def _paragraph_spans(
    text: str,
    start: int,
    end: int,
    ranges: list[tuple[int, int, str, int]],
) -> Iterator[tuple[int, int]]:
    segment = text[start:end]
    cursor = 0
    for boundary in BLANK_LINE_RE.finditer(segment):
        left, right = _drop_leading_headings(
            text,
            start + cursor,
            start + boundary.start(),
            ranges,
        )
        if left < right:
            yield left, right
        cursor = boundary.end()

    left, right = _drop_leading_headings(text, start + cursor, end, ranges)
    if left < right:
        yield left, right


def parse_kaiyuan_passages(
    text: str,
    *,
    source_path: str,
    card_type: str,
    kb_book_id: str = "kaiyuan_zhanjing",
    book_title: str = "唐開元占經",
) -> list[KaiyuanPassage]:
    """Parse Kaiyuan primary text into stable page/paragraph passages.

    Paragraph indices are counted independently for each canonical volume so
    the combined fulltext and split-volume views produce the same logical
    identity.
    """

    if card_type not in PRIMARY_CARD_TYPES:
        raise ValueError("card_type must be fenjuan or fulltext")

    markers = list(PAGE_MARKER_RE.finditer(text))
    ranges = heading_ranges(text)
    segments: list[tuple[int, int, str | None]] = []
    if markers:
        for index, marker in enumerate(markers):
            segment_end = (
                markers[index + 1].start()
                if index + 1 < len(markers)
                else len(text)
            )
            segments.append((marker.end(), segment_end, marker.group(1)))
    else:
        segments.append((0, len(text), None))

    paragraph_counts: dict[str, int] = {}
    output: list[KaiyuanPassage] = []
    for segment_start, segment_end, page_marker in segments:
        source_locator = canonical_source_locator(source_path, page_marker)
        source_volume = source_volume_for_locator(source_locator)
        for raw_start, raw_end in _paragraph_spans(
            text,
            segment_start,
            segment_end,
            ranges,
        ):
            raw_text = text[raw_start:raw_end]
            normalized_text = normalize_search_text(raw_text)
            if not normalized_text:
                continue

            paragraph_index = paragraph_counts.get(source_locator, 0)
            paragraph_counts[source_locator] = paragraph_index + 1
            output.append(
                KaiyuanPassage(
                    kb_book_id=kb_book_id,
                    book_title=book_title,
                    card_type=card_type,
                    source_path=source_path,
                    source_locator=source_locator,
                    source_volume=source_volume,
                    page_marker=page_marker,
                    heading_path=heading_path_at(text, raw_start),
                    paragraph_index=paragraph_index,
                    raw_start=raw_start,
                    raw_end=raw_end,
                    raw_text=raw_text,
                    normalized_text=normalized_text,
                    raw_content_hash=_sha256_text(raw_text),
                    normalized_content_hash=_sha256_text(normalized_text),
                )
            )
    return output


def dedupe_kaiyuan_passages(
    passages: list[KaiyuanPassage],
) -> list[KaiyuanPassage]:
    """Prefer split-volume evidence and retain duplicate fulltext provenance."""

    priority = {"fenjuan": 0, "fulltext": 1}
    ordered = sorted(
        passages,
        key=lambda passage: (
            passage.kb_book_id,
            passage.source_locator,
            passage.page_marker or "",
            passage.paragraph_index,
            priority.get(passage.card_type, 99),
            passage.source_path,
        ),
    )
    by_key: dict[tuple[str, str, str, int, str], KaiyuanPassage] = {}
    output: list[KaiyuanPassage] = []

    for passage in ordered:
        key = (
            passage.kb_book_id,
            passage.source_locator,
            passage.page_marker or "",
            passage.paragraph_index,
            passage.normalized_content_hash,
        )
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = passage
            output.append(passage)
            continue

        duplicate_sources = tuple(
            dict.fromkeys((*existing.duplicate_sources, passage.source_path))
        )
        updated = replace(existing, duplicate_sources=duplicate_sources)
        by_key[key] = updated
        output[output.index(existing)] = updated

    return output
