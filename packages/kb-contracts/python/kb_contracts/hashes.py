from __future__ import annotations

import hashlib

from .normalize import normalize_term


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def stable_candidate_id(kb_book_id: str, term: str, source_locator: str, match_offset: int | str) -> str:
    return f"{kb_book_id}:{normalize_term(term)}:{source_locator}:{int(match_offset)}"
