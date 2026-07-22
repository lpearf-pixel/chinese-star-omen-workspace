from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.video_pipeline.asterisms import load_asterism_catalog


APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parents[1]
CATALOG_PATH = APP_ROOT / "data" / "video_pipeline" / "asterism_catalog_v1.yaml"
SOURCE_ROOT = APP_ROOT / "data" / "video_pipeline" / "sources"
FIXTURE_ROOT = WORKSPACE_ROOT / "tests" / "fixtures" / "asterisms" / "v1"


def canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def test_catalog_sources_bind_committed_snapshot_bytes() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog

    for source in catalog.sources:
        assert source.content_hash_algorithm == "sha256"
        snapshot_path = APP_ROOT / source.snapshot_path
        assert snapshot_path.is_file()
        snapshot_bytes = snapshot_path.read_bytes()
        assert hashlib.sha256(snapshot_bytes).hexdigest() == source.content_hash
        payload = json.loads(snapshot_bytes)
        assert snapshot_bytes == canonical_json_bytes(payload)
        assert payload["source_id"] == source.source_id
        assert payload["revision"] == source.revision


def test_stellarium_source_separates_snapshot_hash_from_upstream_git_blob() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog
    source = next(
        item
        for item in catalog.sources
        if item.source_id == "source:stellarium-chinese-skyculture"
    )

    assert source.upstream_content_id_algorithm == "git-sha1"
    assert source.upstream_content_id == "fe8761576dc6c5cd4a65e3551a81ead6122c895f"
    assert source.content_hash_algorithm == "sha256"
    assert len(source.content_hash) == 64


def test_simbad_snapshot_coordinates_match_catalog_identity() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog
    entry = catalog.entry("hip:65474")
    source = next(item for item in catalog.sources if item.source_id == "source:simbad-spica")
    payload = json.loads((APP_ROOT / source.snapshot_path).read_text(encoding="utf-8"))

    assert payload["identifier"] == "HIP 65474 / Spica"
    assert payload["reference_frame"] == "ICRS J2000"
    assert payload["ra_hms"] == "13 25 11.57937"
    assert payload["dec_dms"] == "-11 09 40.7501"
    assert entry.reference_coordinates.ra_deg == pytest.approx(payload["ra_deg"], abs=1e-12)
    assert entry.reference_coordinates.dec_deg == pytest.approx(payload["dec_deg"], abs=1e-12)


def test_asterism_fixture_manifest_binds_spica_identity_fixture() -> None:
    manifest_path = FIXTURE_ROOT / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)

    assert manifest_bytes == canonical_json_bytes(manifest)
    assert manifest["schema_version"] == "asterism-fixture-manifest/v1"
    assert len(manifest["fixtures"]) == 1
    fixture = manifest["fixtures"][0]
    fixture_path = FIXTURE_ROOT / fixture["path"]
    assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == fixture["sha256"]
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert payload["modern_object_id"] == "hip:65474"
    assert payload["canonical_chinese_name"] == "角宿一"
    assert payload["source_snapshot_sha256"] == {
        item.source_id: item.content_hash for item in load_asterism_catalog(CATALOG_PATH).catalog.sources
    }
