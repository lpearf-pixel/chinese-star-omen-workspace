from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NormalizedText:
    compact: str
    index_map: list[int]


@dataclass(frozen=True)
class MatchSpan:
    start: int
    end: int
    match_type: str
    matched_variant: str
    normalized_variant: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "match_type": self.match_type,
            "matched_variant": self.matched_variant,
            "normalized_variant": self.normalized_variant,
            "score": self.score,
        }


@dataclass(frozen=True)
class AnchorContext:
    page_marker: str | None
    heading_path: list[str]
    paragraph_index: int
    anchor_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_marker": self.page_marker,
            "heading_path": list(self.heading_path),
            "paragraph_index": self.paragraph_index,
            "anchor_text": self.anchor_text,
        }


@dataclass
class MatchCluster:
    spans: list[MatchSpan] = field(default_factory=list)
    context: AnchorContext | None = None

    @property
    def start(self) -> int:
        return min(span.start for span in self.spans)

    @property
    def end(self) -> int:
        return max(span.end for span in self.spans)


@dataclass(frozen=True)
class KaiyuanPassage:
    """A raw, independently addressable primary-evidence passage."""

    kb_book_id: str
    book_title: str
    card_type: str
    source_path: str
    source_locator: str
    source_volume: str | None
    page_marker: str | None
    heading_path: list[str]
    paragraph_index: int
    raw_start: int
    raw_end: int
    raw_text: str
    normalized_text: str
    raw_content_hash: str
    normalized_content_hash: str
    duplicate_sources: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
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
