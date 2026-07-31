from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any, Iterable

from .models import KaiyuanPassage
from .passages import dedupe_kaiyuan_passages


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _anchor(passage: KaiyuanPassage) -> tuple[str, str, str, int]:
    return (
        passage.kb_book_id,
        passage.source_locator,
        passage.page_marker or "",
        passage.paragraph_index,
    )


def _passage_id(passage: KaiyuanPassage) -> str:
    identity = {
        "anchor": _anchor(passage),
        "normalized_content_hash": passage.normalized_content_hash,
    }
    return "passage:sha256:" + hashlib.sha256(_canonical_bytes(identity)).hexdigest()


@dataclass(frozen=True)
class RulePassageRecord:
    passage_id: str
    kb_book_id: str
    book_title: str
    card_type: str
    source_path: str
    source_locator: str
    source_volume: str | None
    page_marker: str | None
    heading_path: tuple[str, ...]
    paragraph_index: int
    raw_start: int
    raw_end: int
    raw_text: str
    normalized_text: str
    raw_content_hash: str
    normalized_content_hash: str
    duplicate_sources: tuple[str, ...]

    @property
    def anchor(self) -> tuple[str, str, str, int]:
        return (
            self.kb_book_id,
            self.source_locator,
            self.page_marker or "",
            self.paragraph_index,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "passage_id": self.passage_id,
            "kb_book_id": self.kb_book_id,
            "book_title": self.book_title,
            "card_type": self.card_type,
            "source_path": self.source_path,
            "source_locator": self.source_locator,
            "source_volume": self.source_volume,
            "page_marker": self.page_marker,
            "heading_path": list(self.heading_path),
            "paragraph_index": self.paragraph_index,
            "raw_start": self.raw_start,
            "raw_end": self.raw_end,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "raw_content_hash": self.raw_content_hash,
            "normalized_content_hash": self.normalized_content_hash,
            "duplicate_sources": list(self.duplicate_sources),
        }


@dataclass(frozen=True)
class AmbiguousAnchor:
    kb_book_id: str
    source_locator: str
    page_marker: str | None
    paragraph_index: int
    passage_ids: tuple[str, ...]


@dataclass(frozen=True)
class ChangedPassage:
    anchor: tuple[str, str, str, int]
    previous_passage_id: str
    current_passage_id: str


@dataclass(frozen=True)
class SourceChangeReport:
    status: str
    invalidated_passage_ids: tuple[str, ...]
    unchanged_passage_ids: tuple[str, ...]
    added_passage_ids: tuple[str, ...]
    removed_passage_ids: tuple[str, ...]
    changed: tuple[ChangedPassage, ...]
    ambiguous_anchors: tuple[tuple[str, str, str, int], ...]


def build_passage_records(
    passages: Iterable[KaiyuanPassage],
) -> tuple[tuple[RulePassageRecord, ...], tuple[AmbiguousAnchor, ...]]:
    normalized = [
        replace(
            item,
            source_path=item.source_path.replace("\\", "/"),
            duplicate_sources=tuple(
                path.replace("\\", "/") for path in item.duplicate_sources
            ),
        )
        for item in passages
    ]
    deduped = dedupe_kaiyuan_passages(normalized)
    records = [
        RulePassageRecord(
            passage_id=_passage_id(item),
            kb_book_id=item.kb_book_id,
            book_title=item.book_title,
            card_type=item.card_type,
            source_path=item.source_path,
            source_locator=item.source_locator,
            source_volume=item.source_volume,
            page_marker=item.page_marker,
            heading_path=tuple(item.heading_path),
            paragraph_index=item.paragraph_index,
            raw_start=item.raw_start,
            raw_end=item.raw_end,
            raw_text=item.raw_text,
            normalized_text=item.normalized_text,
            raw_content_hash=item.raw_content_hash,
            normalized_content_hash=item.normalized_content_hash,
            duplicate_sources=tuple(item.duplicate_sources),
        )
        for item in deduped
    ]
    records.sort(key=lambda item: (item.anchor, item.passage_id))

    by_anchor: dict[tuple[str, str, str, int], list[RulePassageRecord]] = {}
    for record in records:
        by_anchor.setdefault(record.anchor, []).append(record)
    ambiguities = tuple(
        AmbiguousAnchor(
            kb_book_id=anchor[0],
            source_locator=anchor[1],
            page_marker=anchor[2] or None,
            paragraph_index=anchor[3],
            passage_ids=tuple(item.passage_id for item in group),
        )
        for anchor, group in sorted(by_anchor.items())
        if len(group) > 1
    )
    return tuple(records), ambiguities


def compare_passage_records(
    previous: Iterable[RulePassageRecord],
    current: Iterable[RulePassageRecord],
) -> SourceChangeReport:
    previous_by_anchor: dict[
        tuple[str, str, str, int], list[RulePassageRecord]
    ] = {}
    current_by_anchor: dict[
        tuple[str, str, str, int], list[RulePassageRecord]
    ] = {}
    for item in previous:
        previous_by_anchor.setdefault(item.anchor, []).append(item)
    for item in current:
        current_by_anchor.setdefault(item.anchor, []).append(item)

    ambiguous = tuple(
        sorted(
            anchor
            for anchor in set(previous_by_anchor) | set(current_by_anchor)
            if len(previous_by_anchor.get(anchor, ())) > 1
            or len(current_by_anchor.get(anchor, ())) > 1
        )
    )
    unchanged: list[str] = []
    added: list[str] = []
    removed: list[str] = []
    changed: list[ChangedPassage] = []
    for anchor in sorted(set(previous_by_anchor) | set(current_by_anchor)):
        before = previous_by_anchor.get(anchor, [])
        after = current_by_anchor.get(anchor, [])
        if len(before) != 1 or len(after) != 1:
            removed.extend(item.passage_id for item in before)
            added.extend(item.passage_id for item in after)
            continue
        if before[0].passage_id == after[0].passage_id:
            unchanged.append(before[0].passage_id)
        else:
            changed.append(
                ChangedPassage(
                    anchor=anchor,
                    previous_passage_id=before[0].passage_id,
                    current_passage_id=after[0].passage_id,
                )
            )
    status = (
        "unchanged"
        if not added and not removed and not changed and not ambiguous
        else "source_changed"
    )
    return SourceChangeReport(
        status=status,
        invalidated_passage_ids=tuple(
            sorted(
                {
                    *removed,
                    *(item.previous_passage_id for item in changed),
                }
            )
        ),
        unchanged_passage_ids=tuple(sorted(unchanged)),
        added_passage_ids=tuple(sorted(added)),
        removed_passage_ids=tuple(sorted(removed)),
        changed=tuple(changed),
        ambiguous_anchors=ambiguous,
    )
