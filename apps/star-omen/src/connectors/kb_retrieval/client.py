from __future__ import annotations

from typing import Any

from .core import RetrievalCoreMixin
from .transport import KBSearchError, TransportMixin
from .two_stage import TwoStageMixin


class KBSearchRetriever(TwoStageMixin, RetrievalCoreMixin, TransportMixin):
    """Unified downstream client for official retrieval plus local primary fallback."""

    @staticmethod
    def _canonicalize_filters(filters: dict[str, Any] | None) -> dict[str, Any] | None:
        """Accept the v1 alias while making the canonical value available.

        TransportMixin removes the legacy alias from the actual HTTP JSON body.
        Keeping it in the in-process representation avoids breaking downstream
        extensions that still inspect `book_id` during the v2 transition.
        """
        if not filters:
            return None
        canonical = dict(filters)
        if "book_id" in canonical and "kb_book_id" not in canonical:
            canonical["kb_book_id"] = canonical["book_id"]
        return canonical


__all__ = ["KBSearchError", "KBSearchRetriever"]
