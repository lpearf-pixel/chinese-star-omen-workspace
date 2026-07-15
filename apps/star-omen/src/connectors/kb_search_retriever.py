"""Compatibility facade for the refactored KB retrieval client."""

from src.connectors.kb_retrieval import KBSearchError, KBSearchRetriever

__all__ = ["KBSearchError", "KBSearchRetriever"]
