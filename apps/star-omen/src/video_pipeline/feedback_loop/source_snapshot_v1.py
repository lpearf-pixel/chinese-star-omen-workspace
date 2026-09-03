from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Self

from src.connectors.primary_passage_cache import (
    PrimarySourceSnapshot,
    build_primary_source_snapshot,
)
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalKBSourceFileV1,
    LocalKBSourceSnapshotV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
    SourceSnapshotBindingV1,
    canonical_contract_sha256,
)


MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 512 * 1024 * 1024
_READ_CHUNK_BYTES = 1024 * 1024
_StatIdentity = tuple[int, int, int, int]


def _fail(code: ReadOnlyErrorCode = ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED) -> None:
    raise ReadOnlyAdapterError(code)


def _stat_identity(value: os.stat_result) -> _StatIdentity:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)


def _eligible_card_type(relative_path: str) -> str | None:
    normalized = f"/{relative_path}"
    if not relative_path.endswith(".md"):
        return None
    if "/分卷/" in normalized:
        return "fenjuan"
    if "全文合併版" in normalized or "全文合并版" in normalized:
        return "fulltext"
    return None


def _canonical_relative(path: str | Path, *, root: Path) -> str:
    raw = str(path)
    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(root)
        except ValueError:
            _fail()
    value = candidate.as_posix()
    pure = PurePosixPath(value)
    if (
        not value
        or raw.startswith("~")
        or "\\" in raw
        or "//" in value
        or value.startswith("/")
        or pure.as_posix() != value
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        _fail()
    return value


def _canonical_tree_hash(files: tuple[LocalKBSourceFileV1, ...]) -> str:
    payload = [item.model_dump(mode="json") for item in files]
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class LocalKBSourceAccessor:
    """Descriptor-rooted immutable view of one caller-attested source tree."""

    def __init__(
        self,
        *,
        root_fd: int,
        canonical_root: Path,
        root_identity: _StatIdentity,
        snapshot: LocalKBSourceSnapshotV1,
    ) -> None:
        self._root_fd = root_fd
        self._canonical_root = canonical_root
        self._root_identity = root_identity
        self._snapshot = snapshot
        self._snapshot_sha256 = canonical_contract_sha256(snapshot)
        self._files = {item.relative_path: item for item in snapshot.files}
        self._baseline_identities: dict[str, _StatIdentity] = {}
        self._bound = False
        self._closed = False
        self._binding = SourceSnapshotBindingV1(
            canonical_kb_root=canonical_root,
            snapshot_sha256=self._snapshot_sha256,
            collection=snapshot.collection,
            kb_book_id=snapshot.kb_book_id,
            corpus_version=snapshot.corpus_version,
        )

    @classmethod
    def open(
        cls,
        *,
        kb_root: Path,
        snapshot: LocalKBSourceSnapshotV1,
    ) -> Self:
        required_flags = ("O_NOFOLLOW", "O_DIRECTORY", "O_NONBLOCK")
        if (
            any(not hasattr(os, name) for name in required_flags)
            or os.open not in os.supports_dir_fd
        ):
            _fail()
        root_fd: int | None = None
        try:
            canonical_root = Path(kb_root).expanduser().resolve(strict=True)
            root_fd = os.open(
                canonical_root,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            )
            root_stat = os.fstat(root_fd)
            if not stat.S_ISDIR(root_stat.st_mode):
                _fail()
            accessor = cls(
                root_fd=root_fd,
                canonical_root=canonical_root,
                root_identity=_stat_identity(root_stat),
                snapshot=snapshot,
            )
            live_files, identities = accessor._live_inventory()
            if (
                live_files != snapshot.files
                or _canonical_tree_hash(live_files) != snapshot.tree_sha256
            ):
                _fail()
            accessor._baseline_identities = identities
            return accessor
        except ReadOnlyAdapterError:
            if root_fd is not None:
                os.close(root_fd)
            raise
        except (OSError, RuntimeError, ValueError):
            if root_fd is not None:
                os.close(root_fd)
            _fail()

    @property
    def binding(self) -> SourceSnapshotBindingV1:
        return self._binding

    def assert_bound(
        self,
        *,
        kb_root: Path,
        snapshot: LocalKBSourceSnapshotV1,
        snapshot_sha256: str,
    ) -> None:
        self._require_open()
        self._bound = False
        try:
            canonical_root = Path(kb_root).expanduser().resolve(strict=True)
            path_stat = os.stat(canonical_root, follow_symlinks=False)
            fd_stat = os.fstat(self._root_fd)
        except OSError:
            _fail(ReadOnlyErrorCode.SNAPSHOT_MISMATCH)
        if (
            canonical_root != self._canonical_root
            or _stat_identity(path_stat) != self._root_identity
            or _stat_identity(fd_stat) != self._root_identity
            or snapshot != self._snapshot
            or snapshot_sha256 != self._snapshot_sha256
            or canonical_contract_sha256(snapshot) != snapshot_sha256
        ):
            _fail(ReadOnlyErrorCode.SNAPSHOT_MISMATCH)
        self._bound = True

    def load(
        self,
        path: str | Path,
        *,
        card_type: str,
        kb_book_id: str,
        book_title: str,
    ) -> PrimarySourceSnapshot:
        self._require_open()
        if not self._bound:
            _fail(ReadOnlyErrorCode.SNAPSHOT_MISMATCH)
        relative_path = _canonical_relative(path, root=self._canonical_root)
        expected = self._files.get(relative_path)
        if (
            expected is None
            or kb_book_id != self._snapshot.kb_book_id
            or card_type != _eligible_card_type(relative_path)
            or not isinstance(book_title, str)
            or not book_title
        ):
            _fail(ReadOnlyErrorCode.SNAPSHOT_MISMATCH)
        raw_bytes, file_stat = self._read_relative(relative_path)
        identity = _stat_identity(file_stat)
        if (
            identity != self._baseline_identities.get(relative_path)
            or len(raw_bytes) != expected.size_bytes
            or hashlib.sha256(raw_bytes).hexdigest() != expected.sha256
        ):
            _fail()
        try:
            return build_primary_source_snapshot(
                raw_bytes,
                path=self._canonical_root / Path(*PurePosixPath(relative_path).parts),
                mtime_ns=file_stat.st_mtime_ns,
                card_type=card_type,
                kb_book_id=kb_book_id,
                book_title=book_title,
            )
        except Exception:
            _fail()

    def relative_paths(self) -> tuple[str, ...]:
        self._require_open()
        return tuple(item.relative_path for item in self._snapshot.files)

    def assert_unchanged(self) -> None:
        self._require_open()
        try:
            path_identity = _stat_identity(
                os.stat(self._canonical_root, follow_symlinks=False)
            )
            descriptor_identity = _stat_identity(os.fstat(self._root_fd))
        except OSError:
            _fail()
        live_files, identities = self._live_inventory()
        if (
            path_identity != self._root_identity
            or descriptor_identity != self._root_identity
            or live_files != self._snapshot.files
            or _canonical_tree_hash(live_files) != self._snapshot.tree_sha256
            or identities != self._baseline_identities
        ):
            _fail()

    def close(self) -> None:
        if not self._closed:
            os.close(self._root_fd)
            self._closed = True
            self._bound = False

    def __enter__(self) -> Self:
        self._require_open()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _require_open(self) -> None:
        if self._closed:
            _fail()

    def _read_relative(self, relative_path: str) -> tuple[bytes, os.stat_result]:
        parts = PurePosixPath(relative_path).parts
        current_fd = os.dup(self._root_fd)
        final_fd: int | None = None
        try:
            for component in parts[:-1]:
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=current_fd,
                )
                os.close(current_fd)
                current_fd = next_fd
            final_fd = os.open(
                parts[-1],
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=current_fd,
            )
            before = os.fstat(final_fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_SOURCE_BYTES:
                _fail()
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(
                    final_fd,
                    min(_READ_CHUNK_BYTES, MAX_SOURCE_BYTES + 1 - total),
                )
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_SOURCE_BYTES:
                    _fail()
            after = os.fstat(final_fd)
            raw_bytes = b"".join(chunks)
            if (
                _stat_identity(before) != _stat_identity(after)
                or len(raw_bytes) != after.st_size
            ):
                _fail()
            return raw_bytes, after
        except ReadOnlyAdapterError:
            raise
        except OSError:
            _fail()
        finally:
            if final_fd is not None:
                os.close(final_fd)
            os.close(current_fd)

    def _live_inventory(
        self,
    ) -> tuple[tuple[LocalKBSourceFileV1, ...], dict[str, _StatIdentity]]:
        files: list[LocalKBSourceFileV1] = []
        identities: dict[str, _StatIdentity] = {}
        total_bytes = 0

        def walk(directory_fd: int, prefix: tuple[str, ...]) -> None:
            nonlocal total_bytes
            try:
                with os.scandir(directory_fd) as iterator:
                    entries = sorted(iterator, key=lambda item: item.name)
            except OSError:
                _fail()
            for entry in entries:
                relative_parts = (*prefix, entry.name)
                relative_path = PurePosixPath(*relative_parts).as_posix()
                try:
                    entry_stat = entry.stat(follow_symlinks=False)
                except OSError:
                    _fail()
                if stat.S_ISDIR(entry_stat.st_mode):
                    child_fd: int | None = None
                    try:
                        child_fd = os.open(
                            entry.name,
                            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory_fd,
                        )
                        if _stat_identity(os.fstat(child_fd)) != _stat_identity(
                            entry_stat
                        ):
                            _fail()
                        walk(child_fd, relative_parts)
                    except ReadOnlyAdapterError:
                        raise
                    except OSError:
                        _fail()
                    finally:
                        if child_fd is not None:
                            os.close(child_fd)
                    continue
                if _eligible_card_type(relative_path) is None:
                    continue
                if not stat.S_ISREG(entry_stat.st_mode):
                    _fail()
                total_bytes += entry_stat.st_size
                if (
                    entry_stat.st_size > MAX_SOURCE_BYTES
                    or total_bytes > MAX_SNAPSHOT_BYTES
                ):
                    _fail()
                raw_bytes, final_stat = self._read_relative(relative_path)
                identity = _stat_identity(final_stat)
                if identity != _stat_identity(entry_stat):
                    _fail()
                files.append(
                    LocalKBSourceFileV1(
                        relative_path=relative_path,
                        size_bytes=len(raw_bytes),
                        sha256=hashlib.sha256(raw_bytes).hexdigest(),
                    )
                )
                identities[relative_path] = identity

        walk(self._root_fd, ())
        files.sort(key=lambda item: item.relative_path)
        return tuple(files), identities
