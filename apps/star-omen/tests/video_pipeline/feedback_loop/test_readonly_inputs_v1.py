from __future__ import annotations

import json
import os
import socket
from copy import deepcopy
from pathlib import Path
from typing import Callable

import pytest

from src.video_pipeline.feedback_loop.readonly_contracts_v1 import ReadOnlyAdapterError, ReadOnlyErrorCode
from src.video_pipeline.feedback_loop.strict_local_files import (
    load_external_audit_v1,
    load_query_plan_v1,
    load_source_snapshot_v1,
)
from tests.video_pipeline.feedback_loop.test_readonly_contracts_v1 import (
    _audit_payload,
    _plan_payload,
    _snapshot_payload,
)


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


Loader = Callable[[Path], object]


def _assert_invalid(loader: Loader, path: Path) -> None:
    with pytest.raises(ReadOnlyAdapterError) as caught:
        loader(path)
    assert caught.value.code is ReadOnlyErrorCode.INVALID_LOCAL_INPUT
    assert str(path) not in str(caught.value)
    assert caught.value.__cause__ is None


def test_query_and_snapshot_load_json_lists_as_immutable_tuples(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    snapshot_path = tmp_path / "snapshot.json"
    _write(plan_path, _plan_payload())
    _write(snapshot_path, _snapshot_payload())

    plan = load_query_plan_v1(plan_path)
    snapshot = load_source_snapshot_v1(snapshot_path)
    assert isinstance(plan.value.requests, tuple)
    assert isinstance(snapshot.value.files, tuple)
    assert plan.raw_sha256 != plan.canonical_sha256


@pytest.mark.parametrize(
    "text",
    [b'{"x": NaN}', b'{"x": Infinity}', b'{"x": 1e999}', b"\xff"],
)
def test_nonfinite_and_non_utf8_json_are_rejected(tmp_path: Path, text: bytes) -> None:
    path = tmp_path / "unsafe.json"
    path.write_bytes(text)
    _assert_invalid(load_query_plan_v1, path)


def test_duplicate_keys_and_excessive_graphs_are_rejected(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema_version":"x","schema_version":"y"}', encoding="utf-8")
    _assert_invalid(load_query_plan_v1, duplicate)

    nested = tmp_path / "nested.json"
    nested.write_text("[" * 65 + "0" + "]" * 65, encoding="utf-8")
    _assert_invalid(load_query_plan_v1, nested)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("research_only", False),
        ("research_only", 1),
        ("grants_rule_authority", True),
        ("grants_rule_authority", 0),
        ("grants_classical_authority", True),
        ("grants_classical_authority", 0),
    ],
)
def test_audit_authority_flags_are_type_exact(
    tmp_path: Path, field: str, value: object
) -> None:
    path = tmp_path / "audit.json"
    invalid = _audit_payload()
    invalid["audit"][field] = value  # type: ignore[index]
    _write(path, invalid)
    _assert_invalid(load_external_audit_v1, path)


@pytest.mark.parametrize(
    "rights_status",
    [
        "metadata_only",
        "quotation_for_research",
        "permission_confirmed",
        "public_domain",
    ],
)
def test_audit_rights_allowlist_accepts_each_allowed_status(
    tmp_path: Path, rights_status: str
) -> None:
    path = tmp_path / "audit.json"
    payload = _audit_payload()
    payload["source"]["captures"][0]["rights_status"] = rights_status  # type: ignore[index]
    _write(path, payload)
    assert load_external_audit_v1(path).value.audit.audit_id == "audit:one"


def test_unreferenced_unknown_capture_rejects_entire_audit(tmp_path: Path) -> None:
    path = tmp_path / "audit.json"
    payload = _audit_payload()
    unknown_capture = deepcopy(payload["source"]["captures"][0])  # type: ignore[index]
    unknown_capture["capture_id"] = "capture:unreferenced"
    unknown_capture["rights_status"] = "unknown"
    payload["source"]["captures"].append(unknown_capture)  # type: ignore[index]
    _write(path, payload)
    with pytest.raises(ReadOnlyAdapterError) as caught:
        load_external_audit_v1(path)
    assert caught.value.code is ReadOnlyErrorCode.RIGHTS_REJECTED
    assert caught.value.__cause__ is None


def test_loader_rejects_symlink_and_oversized_input_without_leaking_path(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.json"
    _write(target, _plan_payload())
    link = tmp_path / "link.json"
    link.symlink_to(target)
    _assert_invalid(load_query_plan_v1, link)

    too_large = tmp_path / "too-large.json"
    too_large.write_bytes(b" " * (256 * 1024 + 1))
    _assert_invalid(load_query_plan_v1, too_large)


@pytest.mark.parametrize(
    ("loader", "payload", "max_bytes"),
    [
        (load_external_audit_v1, _audit_payload, 2 * 1024 * 1024),
        (load_query_plan_v1, _plan_payload, 256 * 1024),
        (load_source_snapshot_v1, _snapshot_payload, 256 * 1024),
    ],
)
def test_all_loaders_accept_exact_size_and_reject_one_byte_over_limit(
    tmp_path: Path,
    loader: Loader,
    payload: Callable[[], dict[str, object]],
    max_bytes: int,
) -> None:
    path = tmp_path / "bounded.json"
    encoded = json.dumps(payload(), ensure_ascii=False).encode("utf-8")
    path.write_bytes(encoded + b" " * (max_bytes - len(encoded)))
    loader(path)
    path.write_bytes(encoded + b" " * (max_bytes - len(encoded) + 1))
    _assert_invalid(loader, path)


def test_loader_opens_once_and_observes_three_descriptor_stats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "plan.json"
    _write(path, _plan_payload())
    import src.video_pipeline.feedback_loop.strict_local_files as module

    real_open = module.os.open
    real_fstat = module.os.fstat
    opens = 0
    fstats = 0

    def counted_open(*args: object, **kwargs: object) -> int:
        nonlocal opens
        opens += 1
        return real_open(*args, **kwargs)

    def counted_fstat(fd: int) -> os.stat_result:
        nonlocal fstats
        fstats += 1
        return real_fstat(fd)

    monkeypatch.setattr(module.os, "open", counted_open)
    monkeypatch.setattr(module.os, "fstat", counted_fstat)
    load_query_plan_v1(path)
    assert opens == 1
    assert fstats == 3


def test_path_replacement_cannot_redirect_the_open_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "plan.json"
    original = json.dumps(_plan_payload()).encode("utf-8")
    path.write_bytes(original)
    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(b"{}")
    import src.video_pipeline.feedback_loop.strict_local_files as module

    original_read = module._read_bounded
    calls = 0

    def replace_after_first_read(fd: int, max_bytes: int) -> bytes:
        nonlocal calls
        calls += 1
        value = original_read(fd, max_bytes)
        if calls == 1:
            os.replace(replacement, path)
        return value

    monkeypatch.setattr(module, "_read_bounded", replace_after_first_read)
    assert load_query_plan_v1(path).raw_bytes == original


@pytest.mark.parametrize("mutation", ["truncate", "rewrite"])
def test_descriptor_mutations_between_reads_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    path = tmp_path / "plan.json"
    _write(path, _plan_payload())
    import src.video_pipeline.feedback_loop.strict_local_files as module

    original_read = module._read_bounded
    calls = 0

    def mutate_after_first_read(fd: int, max_bytes: int) -> bytes:
        nonlocal calls
        calls += 1
        value = original_read(fd, max_bytes)
        if calls == 1:
            if mutation == "truncate":
                path.write_bytes(b"{}")
            else:
                path.write_bytes(value.replace(b"fixture", b"changed"))
        return value

    monkeypatch.setattr(module, "_read_bounded", mutate_after_first_read)
    _assert_invalid(load_query_plan_v1, path)


def test_descriptor_stability_rejects_changed_second_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "plan.json"
    _write(path, _plan_payload())

    import src.video_pipeline.feedback_loop.strict_local_files as module

    original_read = module._read_bounded
    calls = 0

    def changed_read(fd: int, max_bytes: int) -> bytes:
        nonlocal calls
        calls += 1
        data = original_read(fd, max_bytes)
        return data if calls == 1 else data + b" "

    monkeypatch.setattr(module, "_read_bounded", changed_read)
    _assert_invalid(load_query_plan_v1, path)


@pytest.mark.parametrize(
    ("loader", "payload"),
    [
        (load_external_audit_v1, _audit_payload),
        (load_query_plan_v1, _plan_payload),
        (load_source_snapshot_v1, _snapshot_payload),
    ],
)
def test_all_loaders_map_decoder_recursion_and_node_budget_to_fixed_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    loader: Loader,
    payload: Callable[[], dict[str, object]],
) -> None:
    path = tmp_path / "input.json"
    _write(path, payload())
    import src.video_pipeline.feedback_loop.strict_local_files as module

    monkeypatch.setattr(
        module.json,
        "loads",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RecursionError()),
    )
    _assert_invalid(loader, path)

    monkeypatch.undo()
    path.write_text(
        "[" + ",".join("0" for _ in range(100_001)) + "]",
        encoding="utf-8",
    )
    _assert_invalid(loader, path)


def test_fifo_socket_and_device_inputs_are_rejected_without_reading(tmp_path: Path) -> None:
    fifo = tmp_path / "input.fifo"
    os.mkfifo(fifo)
    _assert_invalid(load_query_plan_v1, fifo)

    socket_path = tmp_path / "input.socket"
    try:
        server = socket.socket(socket.AF_UNIX)
    except PermissionError:
        server = None
    if server is not None:
        with server:
            server.bind(str(socket_path))
            _assert_invalid(load_query_plan_v1, socket_path)

    if Path("/dev/null").exists():
        _assert_invalid(load_query_plan_v1, Path("/dev/null"))
