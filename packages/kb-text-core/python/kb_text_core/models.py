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
