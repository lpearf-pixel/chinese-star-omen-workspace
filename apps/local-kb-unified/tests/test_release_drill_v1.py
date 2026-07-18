from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from release_drill import validate_release_drill


TARGET = "local_kb_kaiyuan_v2"
PROTECTED = "local_kb_default"
ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "verify_release_drill.py"
FIXTURE = ROOT / "tests" / "fixtures" / "release_drill_v1.json"


def _manifest(collection: str, version: str) -> dict:
    return {
        "meta_status": "ok",
        "schema_version": "corpus-manifest/v1",
        "corpus_version": version,
        "ingest_run_id": f"ingest_{version}",
        "source_manifest_hash": f"sha256:{version}",
        "collection": collection,
        "created_at": "2026-07-18T12:00:00Z",
        "managed_by": "local-kb-unified/v2",
        "collection_schema": "passage-v2",
    }


def _phase(collection: str, manifest: dict, protected_count: int = 41) -> dict:
    collections = {
        PROTECTED: {
            "exists": True,
            "points_count": protected_count,
            "config_hash": "sha256:protected-config",
        },
    }
    if collection != PROTECTED:
        collections[collection] = {
            "exists": True,
            "points_count": 57,
            "config_hash": f"sha256:{collection}-config",
        }
    return {
        "active_collection": collection,
        "health": {
            "status": "ok",
            "ready": True,
            "checks": {
                "ollama": True,
                "embedding_model": True,
                "qdrant": True,
                "default_collection": True,
                "corpus_manifest": True,
                "manifest_collection_match": True,
            },
        },
        "meta": copy.deepcopy(manifest),
        "smoke": {
            "structured_recall": {"status": "ok", "collection": collection, "hits_count": 2},
            "primary_evidence": {"status": "ok", "collection": collection, "hits_count": 1},
        },
        "collections": collections,
    }


def _document(previous: str = "local_kb_kaiyuan_v1") -> dict:
    previous_manifest = _manifest(previous, "previous")
    release_manifest = _manifest(TARGET, "release")
    return {
        "schema_version": "kaiyuan-release-drill-input/v1",
        "target_collection": TARGET,
        "expected_release_manifest": {
            key: release_manifest[key]
            for key in (
                "schema_version",
                "corpus_version",
                "ingest_run_id",
                "source_manifest_hash",
                "collection",
                "created_at",
                "managed_by",
                "collection_schema",
            )
        },
        "before_switch": _phase(previous, previous_manifest),
        "after_switch": _phase(TARGET, release_manifest),
        "after_rollback": _phase(previous, previous_manifest),
    }


def test_valid_switch_and_rollback_passes_with_strict_json_report():
    report = validate_release_drill(_document())

    assert report["schema_version"] == "kaiyuan-release-drill/v1"
    assert report["status"] == "passed"
    assert report["target_collection"] == TARGET
    assert report["rollback_collection"] == "local_kb_kaiyuan_v1"
    assert report["errors"] == []
    assert all(report["checks"].values())
    json.dumps(report, allow_nan=False)


def test_prior_legacy_read_route_is_restored_without_mutating_its_fingerprint():
    report = validate_release_drill(_document(PROTECTED))

    assert report["status"] == "passed"
    assert report["rollback_collection"] == PROTECTED
    assert report["checks"]["protected_collection_unchanged"] is True


@pytest.mark.parametrize(
    ("mutate", "error_code"),
    [
        (lambda doc: doc.update(target_collection=PROTECTED), "TARGET_COLLECTION_FORBIDDEN"),
        (lambda doc: doc.pop("after_switch"), "PHASE_CONTRACT_INVALID"),
        (lambda doc: doc["after_switch"]["health"].update(ready=False), "RELEASE_HEALTH_UNREADY"),
        (
            lambda doc: doc["after_switch"]["health"]["checks"].update(qdrant=False),
            "RELEASE_HEALTH_UNREADY",
        ),
        (
            lambda doc: doc["expected_release_manifest"].update(source_manifest_hash="sha256:wrong"),
            "RELEASE_MANIFEST_MISMATCH",
        ),
        (
            lambda doc: doc["after_switch"]["meta"].update(meta_status="missing"),
            "RELEASE_MANIFEST_MISMATCH",
        ),
        (
            lambda doc: doc["after_switch"]["smoke"]["primary_evidence"].update(hits_count=0),
            "RELEASE_SMOKE_FAILED",
        ),
        (
            lambda doc: doc["after_switch"]["smoke"]["structured_recall"].update(collection="other"),
            "RELEASE_SMOKE_FAILED",
        ),
        (
            lambda doc: doc["after_rollback"].update(active_collection="other"),
            "ROLLBACK_COLLECTION_MISMATCH",
        ),
        (
            lambda doc: doc["after_rollback"]["meta"].update(corpus_version="wrong"),
            "ROLLBACK_MANIFEST_MISMATCH",
        ),
        (
            lambda doc: doc["after_rollback"]["collections"][PROTECTED].update(points_count=42),
            "PROTECTED_COLLECTION_DRIFT",
        ),
        (
            lambda doc: doc["after_switch"]["collections"].pop(PROTECTED),
            "PROTECTED_COLLECTION_DRIFT",
        ),
    ],
)
def test_invalid_or_unsafe_drill_fails_closed(mutate, error_code):
    document = _document()
    mutate(document)

    report = validate_release_drill(document)

    assert report["status"] == "failed"
    assert error_code in {error["code"] for error in report["errors"]}


def _run_cli(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), "--input", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_committed_fixture_passes_and_emits_strict_json():
    result = _run_cli(FIXTURE)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout, parse_constant=lambda value: pytest.fail(f"non-finite {value}"))
    assert report["status"] == "passed"


def test_cli_valid_failed_drill_exits_one(tmp_path: Path):
    path = tmp_path / "failed.json"
    document = _document()
    document["target_collection"] = PROTECTED
    path.write_text(json.dumps(document), encoding="utf-8")

    result = _run_cli(path)

    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "failed"


def test_cli_invalid_json_exits_two_without_success_report(tmp_path: Path):
    path = tmp_path / "invalid.json"
    path.write_text("{not-json", encoding="utf-8")

    result = _run_cli(path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "release drill input error" in result.stderr


def test_release_target_must_exist_in_observed_collection_snapshot():
    document = _document()
    document["after_switch"]["collections"][TARGET]["exists"] = False

    report = validate_release_drill(document)

    assert report["status"] == "failed"
    assert "RELEASE_COLLECTION_UNAVAILABLE" in {error["code"] for error in report["errors"]}
