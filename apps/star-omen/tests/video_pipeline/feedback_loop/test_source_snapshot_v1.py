from __future__ import annotations

import hashlib
import json
import os
import socket
import stat
from pathlib import Path

import pytest

from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalKBSourceSnapshotV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
    canonical_contract_sha256,
)
from src.video_pipeline.feedback_loop.source_snapshot_v1 import LocalKBSourceAccessor


BOOK_ID = "kaiyuan_zhanjing"
VOLUME = "古籍/唐開元占經/分卷/KR3g0018_031.md"
FULLTEXT = "古籍/唐開元占經/唐開元占經-全文合併版.md"


def _tree_hash(files: list[dict[str, object]]) -> str:
    return hashlib.sha256(
        json.dumps(
            files,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _snapshot(root: Path, paths: tuple[str, ...] = (FULLTEXT, VOLUME)) -> LocalKBSourceSnapshotV1:
    files = []
    for relative_path in sorted(paths):
        raw = (root / relative_path).read_bytes()
        files.append(
            {
                "relative_path": relative_path,
                "size_bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    return LocalKBSourceSnapshotV1.model_validate(
        {
            "schema_version": "local-kb-source-snapshot/v1",
            "snapshot_id": "snapshot:test-source-root",
            "corpus_version": "20260101T000000Z",
            "collection": "local_kb_kaiyuan_v2",
            "kb_book_id": BOOK_ID,
            "files": files,
            "tree_sha256": _tree_hash(files),
        }
    )


def _write_root(root: Path) -> LocalKBSourceSnapshotV1:
    volume = root / VOLUME
    volume.parent.mkdir(parents=True)
    volume.write_text(
        "# 唐開元占經\n<pb:KR3g0018_WYG_031-17a>\n石氏曰畢宿主兵。\n",
        encoding="utf-8",
    )
    fulltext = root / FULLTEXT
    fulltext.write_text(volume.read_text(encoding="utf-8"), encoding="utf-8")
    ignored = root / "古籍" / "唐開元占經" / "notes.md"
    ignored.write_text("not scanner eligible", encoding="utf-8")
    return _snapshot(root)


def _bind(accessor: LocalKBSourceAccessor, root: Path, snapshot: LocalKBSourceSnapshotV1) -> None:
    accessor.assert_bound(
        kb_root=root,
        snapshot=snapshot,
        snapshot_sha256=canonical_contract_sha256(snapshot),
    )


def _assert_integrity_error(callable_) -> None:
    with pytest.raises(ReadOnlyAdapterError) as exc_info:
        callable_()
    assert exc_info.value.code is ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED
    assert str(exc_info.value) == "source_integrity_failed"


def test_accessor_binds_exact_inventory_and_loads_verified_descriptor_bytes(
    tmp_path: Path,
) -> None:
    snapshot = _write_root(tmp_path)

    with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
        assert accessor.relative_paths() == tuple(item.relative_path for item in snapshot.files)
        with pytest.raises(ReadOnlyAdapterError) as exc_info:
            accessor.load(
                VOLUME,
                card_type="fenjuan",
                kb_book_id=BOOK_ID,
                book_title="唐開元占經",
            )
        assert exc_info.value.code is ReadOnlyErrorCode.SNAPSHOT_MISMATCH

        _bind(accessor, tmp_path, snapshot)
        loaded = accessor.load(
            VOLUME,
            card_type="fenjuan",
            kb_book_id=BOOK_ID,
            book_title="唐開元占經",
        )
        manifest_file = next(item for item in snapshot.files if item.relative_path == VOLUME)
        assert loaded.path == tmp_path.resolve() / VOLUME
        assert loaded.size_bytes == manifest_file.size_bytes
        assert loaded.content_hash == f"sha256:{manifest_file.sha256}"
        assert isinstance(loaded.mtime_ns, int)
        assert not isinstance(loaded.mtime_ns, bool)
        assert loaded.passages[0].raw_content_hash.startswith("sha256:")
        accessor.assert_unchanged()


def test_assert_bound_rejects_root_snapshot_and_canonical_hash_mismatch(tmp_path: Path) -> None:
    snapshot = _write_root(tmp_path / "one")
    other_root = tmp_path / "two"
    other_snapshot_payload = _write_root(other_root).model_dump(mode="json")
    other_snapshot_payload["snapshot_id"] = "snapshot:other-source-root"
    other_snapshot = LocalKBSourceSnapshotV1.model_validate(other_snapshot_payload)

    with LocalKBSourceAccessor.open(kb_root=tmp_path / "one", snapshot=snapshot) as accessor:
        for kwargs in (
            {
                "kb_root": other_root,
                "snapshot": snapshot,
                "snapshot_sha256": canonical_contract_sha256(snapshot),
            },
            {
                "kb_root": tmp_path / "one",
                "snapshot": other_snapshot,
                "snapshot_sha256": canonical_contract_sha256(other_snapshot),
            },
            {
                "kb_root": tmp_path / "one",
                "snapshot": snapshot,
                "snapshot_sha256": "0" * 64,
            },
        ):
            with pytest.raises(ReadOnlyAdapterError) as exc_info:
                accessor.assert_bound(**kwargs)
            assert exc_info.value.code is ReadOnlyErrorCode.SNAPSHOT_MISMATCH
            assert str(exc_info.value) == "snapshot_mismatch"


@pytest.mark.parametrize("mutation", ["missing", "extra", "changed", "replaced"])
def test_accessor_rejects_live_inventory_or_identity_changes(
    tmp_path: Path, mutation: str
) -> None:
    snapshot = _write_root(tmp_path)
    target = tmp_path / VOLUME
    original_stat = target.stat()

    with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
        _bind(accessor, tmp_path, snapshot)
        if mutation == "missing":
            target.unlink()
        elif mutation == "extra":
            extra = tmp_path / "古籍" / "唐開元占經" / "分卷" / "KR3g0018_032.md"
            extra.write_text("extra", encoding="utf-8")
        elif mutation == "changed":
            before = target.read_text(encoding="utf-8")
            target.write_text(before.replace("主兵", "主雨"), encoding="utf-8")
            os.utime(target, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
        else:
            replacement = target.with_suffix(".replacement")
            replacement.write_bytes(target.read_bytes())
            replacement.replace(target)

        if mutation == "extra":
            _assert_integrity_error(accessor.assert_unchanged)
        else:
            _assert_integrity_error(
                lambda: accessor.load(
                    VOLUME,
                    card_type="fenjuan",
                    kb_book_id=BOOK_ID,
                    book_title="唐開元占經",
                )
            )


def test_accessor_rejects_symlinked_intermediate_component(tmp_path: Path) -> None:
    real_root = tmp_path / "real"
    snapshot = _write_root(real_root)
    linked_root = tmp_path / "linked"
    linked_root.mkdir()
    (linked_root / "古籍").symlink_to(real_root / "古籍", target_is_directory=True)

    with pytest.raises(ReadOnlyAdapterError) as exc_info:
        LocalKBSourceAccessor.open(kb_root=linked_root, snapshot=snapshot)
    assert exc_info.value.code is ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO unavailable")
def test_special_terminal_entries_fail_without_blocking(tmp_path: Path) -> None:
    snapshot = _write_root(tmp_path)
    target = tmp_path / VOLUME
    target.unlink()
    os.mkfifo(target)

    with pytest.raises(ReadOnlyAdapterError) as exc_info:
        LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot)
    assert exc_info.value.code is ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED


def test_socket_terminal_entry_fails_without_blocking(tmp_path: Path) -> None:
    snapshot = _write_root(tmp_path)
    target = tmp_path / VOLUME
    target.unlink()
    try:
        sock = socket.socket(socket.AF_UNIX)
    except PermissionError:
        pytest.skip("Unix sockets prohibited by the test sandbox")
    try:
        sock.bind(str(target))
        with pytest.raises(ReadOnlyAdapterError) as exc_info:
            LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot)
        assert exc_info.value.code is ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED
    finally:
        sock.close()


@pytest.mark.skipif(not hasattr(os, "mknod"), reason="device creation unavailable")
def test_device_terminal_entry_fails_without_reading(tmp_path: Path) -> None:
    snapshot = _write_root(tmp_path)
    target = tmp_path / VOLUME
    target.unlink()
    try:
        os.mknod(target, stat.S_IFCHR | 0o600, os.makedev(1, 3))
    except PermissionError:
        pytest.skip("device creation prohibited by the test sandbox")

    with pytest.raises(ReadOnlyAdapterError) as exc_info:
        LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot)
    assert exc_info.value.code is ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED


def test_accessor_rejects_wrong_book_and_closed_state(tmp_path: Path) -> None:
    snapshot = _write_root(tmp_path)
    accessor = LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot)
    _bind(accessor, tmp_path, snapshot)

    with pytest.raises(ReadOnlyAdapterError) as exc_info:
        accessor.load(
            VOLUME,
            card_type="fenjuan",
            kb_book_id="wrong_book",
            book_title="唐開元占經",
        )
    assert exc_info.value.code is ReadOnlyErrorCode.SNAPSHOT_MISMATCH

    accessor.close()
    _assert_integrity_error(accessor.assert_unchanged)


def test_total_size_limit_is_enforced_before_hashing(monkeypatch, tmp_path: Path) -> None:
    snapshot = _write_root(tmp_path)
    import src.video_pipeline.feedback_loop.source_snapshot_v1 as module

    monkeypatch.setattr(module, "MAX_SNAPSHOT_BYTES", 1)
    with pytest.raises(ReadOnlyAdapterError) as exc_info:
        LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot)
    assert exc_info.value.code is ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED


def test_per_file_size_limit_is_enforced_independently(
    monkeypatch, tmp_path: Path
) -> None:
    snapshot = _write_root(tmp_path)
    import src.video_pipeline.feedback_loop.source_snapshot_v1 as module

    monkeypatch.setattr(module, "MAX_SOURCE_BYTES", 1)
    monkeypatch.setattr(module, "MAX_SNAPSHOT_BYTES", 1024 * 1024)
    with pytest.raises(ReadOnlyAdapterError) as exc_info:
        LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot)
    assert exc_info.value.code is ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED
