from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.video_pipeline.astronomy import (
    EphemerisFileSpecV1,
    build_toolchain_manifest,
    verify_ephemeris_file,
)
from src.video_pipeline.asterisms import load_asterism_catalog
from src.video_pipeline.astronomy import load_scientific_conventions


APP_ROOT = Path(__file__).resolve().parents[3]
CONVENTIONS_PATH = APP_ROOT / "data" / "video_pipeline" / "scientific_conventions_v1.yaml"
CATALOG_PATH = APP_ROOT / "data" / "video_pipeline" / "asterism_catalog_v1.yaml"


def write_fake_bsp(path: Path, data: bytes = b"DAF/SPK synthetic fixture") -> str:
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def test_ephemeris_verification_accepts_exact_local_file(tmp_path: Path) -> None:
    path = tmp_path / "de421.bsp"
    sha256 = write_fake_bsp(path)
    spec = EphemerisFileSpecV1(
        logical_name="de421.bsp",
        expected_sha256=sha256,
        expected_size_bytes=path.stat().st_size,
        max_size_bytes=1024,
    )

    verified = verify_ephemeris_file(path, spec)

    assert verified.logical_name == "de421.bsp"
    assert verified.sha256 == sha256
    assert verified.byte_size == path.stat().st_size
    assert verified.path == path.resolve()
    assert str(path.resolve()) not in verified.safe_provenance().model_dump_json()


def test_missing_wrong_suffix_size_and_hash_fail_before_load(tmp_path: Path) -> None:
    missing_spec = EphemerisFileSpecV1(
        logical_name="de421.bsp",
        expected_sha256="a" * 64,
        max_size_bytes=1024,
    )
    with pytest.raises(FileNotFoundError):
        verify_ephemeris_file(tmp_path / "missing.bsp", missing_spec)

    wrong_suffix = tmp_path / "de421.dat"
    sha256 = write_fake_bsp(wrong_suffix)
    wrong_suffix_spec = EphemerisFileSpecV1(
        logical_name="de421.bsp",
        expected_sha256=sha256,
        max_size_bytes=1024,
    )
    with pytest.raises(ValueError, match=".bsp"):
        verify_ephemeris_file(wrong_suffix, wrong_suffix_spec)

    path = tmp_path / "de421.bsp"
    sha256 = write_fake_bsp(path)
    wrong_size = EphemerisFileSpecV1(
        logical_name="de421.bsp",
        expected_sha256=sha256,
        expected_size_bytes=path.stat().st_size + 1,
        max_size_bytes=1024,
    )
    with pytest.raises(ValueError, match="size"):
        verify_ephemeris_file(path, wrong_size)

    wrong_hash = EphemerisFileSpecV1(
        logical_name="de421.bsp",
        expected_sha256="b" * 64,
        expected_size_bytes=path.stat().st_size,
        max_size_bytes=1024,
    )
    with pytest.raises(ValueError, match="sha256"):
        verify_ephemeris_file(path, wrong_hash)


def test_ephemeris_spec_rejects_unsafe_values() -> None:
    with pytest.raises(ValidationError):
        EphemerisFileSpecV1(
            logical_name="../de421.bsp",
            expected_sha256="a" * 64,
            max_size_bytes=1024,
        )
    with pytest.raises(ValidationError):
        EphemerisFileSpecV1(
            logical_name="de421.bsp",
            expected_sha256="not-a-hash",
            max_size_bytes=1024,
        )
    with pytest.raises(ValidationError):
        EphemerisFileSpecV1(
            logical_name="de421.bsp",
            expected_sha256="a" * 64,
            max_size_bytes=0,
        )


def test_symlink_and_oversized_ephemeris_are_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.bsp"
    sha256 = write_fake_bsp(target)
    symlink = tmp_path / "linked.bsp"
    symlink.symlink_to(target)
    spec = EphemerisFileSpecV1(
        logical_name="de421.bsp",
        expected_sha256=sha256,
        max_size_bytes=1024,
    )
    with pytest.raises(ValueError, match="symlink"):
        verify_ephemeris_file(symlink, spec)

    oversized = tmp_path / "large.bsp"
    large_sha = write_fake_bsp(oversized, b"x" * 1025)
    large_spec = EphemerisFileSpecV1(
        logical_name="large.bsp",
        expected_sha256=large_sha,
        max_size_bytes=1024,
    )
    with pytest.raises(ValueError, match="too large"):
        verify_ephemeris_file(oversized, large_spec)


def test_toolchain_manifest_is_path_free_and_bound_to_assets(tmp_path: Path) -> None:
    path = tmp_path / "de421.bsp"
    sha256 = write_fake_bsp(path)
    verified = verify_ephemeris_file(
        path,
        EphemerisFileSpecV1(
            logical_name="de421.bsp",
            expected_sha256=sha256,
            expected_size_bytes=path.stat().st_size,
            max_size_bytes=1024,
        ),
    )
    conventions = load_scientific_conventions(CONVENTIONS_PATH)
    catalog = load_asterism_catalog(CATALOG_PATH)

    manifest = build_toolchain_manifest(
        verified_ephemeris=verified,
        conventions=conventions,
        catalog=catalog,
        skyfield_version="1.51",
        skyfield_data_version="7.0.0",
    )
    payload = manifest.model_dump_json()

    assert manifest.schema_version == "astronomy-toolchain/v1"
    assert manifest.ephemeris.sha256 == sha256
    assert manifest.conventions_sha256 == conventions.sha256
    assert manifest.asterism_catalog_sha256 == catalog.sha256
    assert manifest.timescale_source == "skyfield-builtin"
    assert str(path.resolve()) not in payload
    assert "tmp" not in payload
