"""Plain-text chunking shared by ingest source adapters."""

from __future__ import annotations

from typing import List, Tuple


def split_into_chunks(text: str, size: int, overlap: int) -> List[Tuple[int, str]]:
    value = text.strip()
    if not value:
        return []
    chunks: List[Tuple[int, str]] = []
    start = 0
    index = 0
    length = len(value)
    while start < length:
        end = min(start + size, length)
        piece = value[start:end].strip()
        if piece:
            chunks.append((index, piece))
            index += 1
        if end >= length:
            break
        start = max(0, end - overlap)
    return chunks
