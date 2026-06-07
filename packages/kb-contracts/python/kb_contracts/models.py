from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SyncStatus(StrEnum):
    PENDING = "pending"
    MERGED = "merged"
    NEEDS_REVIEW = "needs_review"
    STALE = "stale"


REVIEW_STATUSES = {status.value for status in ReviewStatus}
SYNC_STATUSES = {status.value for status in SyncStatus}


@dataclass
class CandidateManifest:
    schema_version: str = "candidate-manifest/v1"
    source_project: str = "Codex-ready-chinese-star-omen-project"
    target_upstream: str = "Local-KB-Unified"
    book_id: str = ""
    base_corpus_version: str = "unknown"
    base_ingest_run_id: str = "unknown"
    current_upstream_corpus_version: str | None = None
    last_synced_at: str | None = None
    items: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_project": self.source_project,
            "target_upstream": self.target_upstream,
            "book_id": self.book_id,
            "base_corpus_version": self.base_corpus_version,
            "base_ingest_run_id": self.base_ingest_run_id,
            "current_upstream_corpus_version": self.current_upstream_corpus_version,
            "last_synced_at": self.last_synced_at,
            "items": self.items,
        }
