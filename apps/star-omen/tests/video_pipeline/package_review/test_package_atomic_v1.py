from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.video_pipeline.package import (
    build_package_manifest,
    verify_package_members,
    write_package_atomic,
)


def members() -> dict[str, bytes]:
    return {
        "astronomy-event.json": b'{"schema_version":"astronomy-event/v1"}\n',
        "editorial-package.json": b'{"schema_version":"editorial-package/v1"}\n',
        "scene.ssc": b'core.clear("natural");\n',
        "subtitles.srt": b"1\n00:00:00,000 --> 00:00:01,000\nTest\n",
    }


def test_manifest_is_deterministic_content_bound_and_path_free() -> None:
    first = build_package_manifest(
        package_id="package:test-atomic-v1",
        members=members(),
    )
    second = build_package_manifest(
        package_id="package:test-atomic-v1",
        members=dict(reversed(list(members().items()))),
    )

    assert first == second
    assert [entry.path for entry in first.members] == sorted(members())
    assert all(len(entry.sha256) == 64 for entry in first.members)
    assert all(entry.byte_size == len(members()[entry.path]) for entry in first.members)
    assert "/Users/" not in first.model_dump_json()
    assert verify_package_members(first, members()) is True

    tampered = dict(members())
    tampered["scene.ssc"] += b"tampered\n"
    with pytest.raises((ValidationError, ValueError), match="hash|size|member"):
        verify_package_members(first, tampered)


def test_atomic_writer_publishes_only_after_validation_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    manifest = build_package_manifest(
        package_id="package:test-atomic-v1",
        members=members(),
    )
    output = tmp_path / "vertical-package"

    published = write_package_atomic(
        output_dir=output,
        manifest=manifest,
        members=members(),
    )

    assert published == output
    assert output.is_dir()
    assert (output / "manifest.json").is_file()
    assert (output / "scene.ssc").read_bytes() == members()["scene.ssc"]
    assert not list(tmp_path.glob(".vertical-package.*"))

    with pytest.raises(FileExistsError):
        write_package_atomic(
            output_dir=output,
            manifest=manifest,
            members=members(),
        )


def test_atomic_writer_leaves_no_output_or_staging_on_failure(tmp_path: Path) -> None:
    manifest = build_package_manifest(
        package_id="package:test-atomic-v1",
        members=members(),
    )
    tampered = dict(members())
    tampered["subtitles.srt"] += b"tampered"
    output = tmp_path / "vertical-package"

    with pytest.raises((ValidationError, ValueError), match="hash|size|member"):
        write_package_atomic(
            output_dir=output,
            manifest=manifest,
            members=tampered,
        )

    assert not output.exists()
    assert not list(tmp_path.glob(".vertical-package.*"))


@pytest.mark.parametrize(
    "unsafe_path",
    ["../escape.json", "/tmp/escape.json", "nested/../../escape.json", "", "."],
)
def test_manifest_rejects_unsafe_member_paths(unsafe_path: str) -> None:
    payload = members()
    payload[unsafe_path] = b"unsafe"
    with pytest.raises((ValidationError, ValueError), match="path|member|relative"):
        build_package_manifest(
            package_id="package:test-atomic-v1",
            members=payload,
        )


def test_structured_package_size_is_bounded() -> None:
    oversized = {"oversized.json": b"x" * (10 * 1024 * 1024 + 1)}
    with pytest.raises((ValidationError, ValueError), match="10 MiB|size|large"):
        build_package_manifest(
            package_id="package:test-atomic-v1",
            members=oversized,
        )
