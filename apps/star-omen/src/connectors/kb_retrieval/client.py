from __future__ import annotations

from typing import Any

from .core import RetrievalCoreMixin
from .transport import KBSearchError, TransportMixin
from .two_stage import TwoStageMixin


class KBSearchRetriever(TwoStageMixin, RetrievalCoreMixin, TransportMixin):
    """Unified downstream client for official retrieval plus local primary fallback."""

    @staticmethod
    def _canonicalize_filters(
        filters: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Write only canonical filter names and reject conflicting aliases."""

        if not filters:
            return None
        canonical = dict(filters)
        legacy = canonical.get("book_id")
        current = canonical.get("kb_book_id")
        if legacy is not None and current is not None and str(legacy) != str(current):
            raise ValueError("conflicting book identifiers: book_id and kb_book_id")
        if current is None and legacy is not None:
            canonical["kb_book_id"] = legacy
        canonical.pop("book_id", None)
        return canonical


__all__ = ["KBSearchError", "KBSearchRetriever"]
