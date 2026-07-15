from __future__ import annotations

from .core import RetrievalCoreMixin
from .transport import KBSearchError, TransportMixin
from .two_stage import TwoStageMixin


class KBSearchRetriever(TwoStageMixin, RetrievalCoreMixin, TransportMixin):
    """Unified downstream client for official retrieval plus local primary fallback."""


__all__ = ["KBSearchError", "KBSearchRetriever"]
