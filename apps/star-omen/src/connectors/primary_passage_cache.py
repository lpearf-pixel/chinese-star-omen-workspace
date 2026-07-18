from __future__ import annotations

import hashlib
from collections import OrderedDict
from dataclasses import dataclass, replace
from pathlib import Path
from threading import RLock
from typing import Any

from kb_text_core import parse_kaiyuan_passages


class PrimarySourceReadError(RuntimeError):
    """Raised when a primary source cannot produce a stable strict snapshot."""


@dataclass(frozen=True)
class PrimarySourceSnapshot:
    path: Path
    mtime_ns: int
    size_bytes: int
    content_hash: str
    text: str
    passages: tuple[Any, ...]


ParserIdentity = tuple[str, str, str]
CacheKey = tuple[Path, ParserIdentity]


class PrimaryPassageCache:
    """Bounded process-local cache of immutable primary source snapshots."""

    def __init__(self, max_entries: int = 128) -> None:
        if isinstance(max_entries, bool) or not isinstance(max_entries, int) or max_entries <= 0:
            raise ValueError("max_entries must be a positive integer")
        self.max_entries = max_entries
        self._entries: OrderedDict[CacheKey, PrimarySourceSnapshot] = OrderedDict()
        self._lock = RLock()

    @staticmethod
    def _read_stable_bytes(path: Path) -> tuple[bytes, Any]:
        last_error: OSError | None = None
        for _attempt in range(2):
            try:
                before = path.stat()
                content = path.read_bytes()
                after = path.stat()
            except OSError as exc:
                last_error = exc
                continue
            before_identity = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
            )
            after_identity = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            )
            if before_identity == after_identity and len(content) == after.st_size:
                return content, after
        detail = str(last_error) if last_error is not None else "source_changed_during_read"
        raise PrimarySourceReadError(f"source_read_failed:{path}:{detail}")

    def load(
        self,
        path: str | Path,
        *,
        card_type: str,
        kb_book_id: str,
        book_title: str,
    ) -> PrimarySourceSnapshot:
        resolved = Path(path).expanduser().resolve()
        identity: ParserIdentity = (card_type, kb_book_id, book_title)
        key: CacheKey = (resolved, identity)

        with self._lock:
            raw_bytes, stat = self._read_stable_bytes(resolved)
            try:
                text = raw_bytes.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                raise PrimarySourceReadError(
                    f"source_decode_failed:{resolved}:{exc}"
                ) from exc
            content_hash = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
            cached = self._entries.get(key)
            if cached is not None and cached.content_hash == content_hash:
                if cached.mtime_ns != stat.st_mtime_ns or cached.size_bytes != stat.st_size:
                    cached = replace(
                        cached,
                        mtime_ns=stat.st_mtime_ns,
                        size_bytes=stat.st_size,
                    )
                    self._entries[key] = cached
                self._entries.move_to_end(key)
                return cached

            passages = tuple(
                parse_kaiyuan_passages(
                    text,
                    source_path=str(resolved),
                    card_type=card_type,
                    kb_book_id=kb_book_id,
                    book_title=book_title,
                )
            )
            snapshot = PrimarySourceSnapshot(
                path=resolved,
                mtime_ns=stat.st_mtime_ns,
                size_bytes=stat.st_size,
                content_hash=content_hash,
                text=text,
                passages=passages,
            )
            self._entries[key] = snapshot
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
            return snapshot

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


primary_passage_cache = PrimaryPassageCache()
