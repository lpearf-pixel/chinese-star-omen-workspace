from __future__ import annotations

from pathlib import Path

import pytest

from src.video_pipeline.package import (
    _publish_directory_noreplace,
    build_package_manifest,
)


def test_directory_publish_never_replaces_existing_empty_target(tmp_path: Path) -> None:
    staging = tmp_path / ".package.staging"
    output = tmp_path / "package"
    staging.mkdir()
    (staging / "member.txt").write_text("new", encoding="utf-8")
    output.mkdir()
    (output / "sentinel.txt").write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        _publish_directory_noreplace(staging, output)

    assert staging.is_dir()
    assert (output / "sentinel.txt").read_text(encoding="utf-8") == "existing"


def test_manifest_rejects_noncanonical_member_spelling() -> None:
    with pytest.raises((ValueError, TypeError), match="canonical|path|member"):
        build_package_manifest(
            package_id="package:noncanonical-v1",
            members={"nested//member.json": b"{}\n"},
        )
