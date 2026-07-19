from __future__ import annotations

import re
from uuid import uuid4

import pytest

from release_artifact import ReleaseArtifactError
from release_artifact import assemble_release_artifact
from release_evidence_bundle import create_bundle_bytes, verify_bundle_bytes
from release_observation import capture_phase_observation
from release_drill import MANIFEST_IDENTITY_FIELDS, PROTECTED_COLLECTION


TARGET = "local_kb_kaiyuan_v2"
TIMES = {
    "before_switch": "2026-07-18T12:00:00Z",
    "after_switch": "2026-07-18T12:05:00Z",
    "after_rollback": "2026-07-18T12:10:00Z",
}


def _manifest(collection: str, *, release: bool) -> dict[str, str]:
    marker = "a" if release else "b"
    return {
        "schema_version": "corpus-manifest/v1",
        "corpus_version": "release" if release else "previous",
        "ingest_run_id": "ingest_release" if release else "ingest_previous",
        "source_manifest_hash": "sha256:" + marker * 64,
        "collection": collection,
        "created_at": "2026-07-18T11:00:00Z" if release else "2026-07-17T11:00:00Z",
        "managed_by": "local-kb-unified/v2",
        "collection_schema": "passage-v2",
    }


def _capture(
    phase_name: str,
    active_collection: str,
    manifest: dict[str, str],
    operations: list[tuple[str, str, str]],
) -> dict[str, object]:
    def health():
        operations.append((phase_name, "health", active_collection))
        return {
            "http_status": 200,
            "body": {
                "status": "ok",
                "ready": True,
                "default_collection": active_collection,
                "checks": {
                    "ollama": True,
                    "embedding_model": True,
                    "qdrant": True,
                    "default_collection": True,
                    "corpus_manifest": True,
                    "manifest_collection_match": True,
                },
            },
        }

    def meta():
        operations.append((phase_name, "meta", active_collection))
        return {"http_status": 200, "body": {"meta_status": "ok", **manifest}}

    def retrieve(**request):
        stage = request["retrieval_stage"]
        operations.append((phase_name, stage, request["collection"]))
        count = 2 if stage == "structured_recall" else 1
        return {
            "http_status": 200,
            "body": {
                "retrieval_stage": stage,
                "card_types": request["card_types"],
                "collection": request["collection"],
                "retrieved_count": count,
                "hits": [{} for _ in range(count)],
            },
        }

    def inspect(collection: str):
        operations.append((phase_name, "inspect", collection))
        return {
            "exists": True,
            "points_count": 41 if collection == PROTECTED_COLLECTION else 57,
            "config": {"vectors": {"size": 768, "distance": "Cosine"}, "shard_number": 1},
        }

    observation = capture_phase_observation(
        active_collection=active_collection,
        query="熒惑守心",
        fetch_health=health,
        fetch_meta=meta,
        retrieve=retrieve,
        inspect_collection=inspect,
        captured_at=TIMES[phase_name],
    )
    observation["phase_name"] = phase_name
    return observation


def _run_release_evidence_gate(*, tamper_after_switch: bool = False) -> dict[str, object]:
    prior = "ephemeral_kaiyuan_release_" + uuid4().hex
    assert re.fullmatch(r"ephemeral_kaiyuan_release_[0-9a-f]{32}", prior)
    operations: list[tuple[str, str, str]] = []
    previous_manifest = _manifest(prior, release=False)
    release_manifest = _manifest(TARGET, release=True)
    observations = {
        "before_switch": _capture("before_switch", prior, previous_manifest, operations),
        "after_switch": _capture("after_switch", TARGET, release_manifest, operations),
        "after_rollback": _capture("after_rollback", prior, previous_manifest, operations),
    }
    if tamper_after_switch:
        observations["after_switch"]["phase"]["meta"]["source_manifest_hash"] = "sha256:" + "c" * 64
    expected_manifest = {name: release_manifest[name] for name in MANIFEST_IDENTITY_FIELDS}
    assembled, report = assemble_release_artifact(
        observations=observations,
        expected_manifest=expected_manifest,
    )
    bundle, created = create_bundle_bytes(
        observations=observations,
        expected_manifest=expected_manifest,
        assembled_document=assembled,
        release_head="1" * 40,
        created_at="2026-07-18T12:15:00Z",
    )
    allowed = {"health", "meta", "structured_recall", "primary_evidence", "inspect"}
    assert all(operation in allowed for _, operation, _ in operations)
    assert all(collection in {prior, TARGET, PROTECTED_COLLECTION} for _, _, collection in operations)
    return {
        "prior": prior,
        "operations": operations,
        "report": report,
        "created": created,
        "verified": verify_bundle_bytes(bundle),
    }


def test_release_evidence_pipeline_is_hermetic_read_only_and_verified():
    result = _run_release_evidence_gate()

    assert result["report"]["schema_version"] == "kaiyuan-release-drill/v1"
    assert result["report"]["status"] == "passed"
    assert result["report"]["errors"] == []
    assert all(result["report"]["checks"].values())
    assert result["created"]["status"] == "created"
    assert result["verified"] == {
        "schema_version": "kaiyuan-release-evidence-bundle/v1",
        "status": "verified",
        "release_head": "1" * 40,
        "target_collection": "local_kb_kaiyuan_v2",
        "member_count": 7,
    }


def test_release_evidence_pipeline_fails_closed_before_bundle_on_manifest_tamper():
    with pytest.raises(ReleaseArtifactError) as caught:
        _run_release_evidence_gate(tamper_after_switch=True)

    assert (caught.value.code, caught.value.field) == ("drill_validation_failed", "document")


def test_protected_fingerprint_is_inspected_once_in_each_fake_phase():
    operations = _run_release_evidence_gate()["operations"]

    protected = [phase for phase, operation, collection in operations if operation == "inspect" and collection == PROTECTED_COLLECTION]
    assert protected == ["before_switch", "after_switch", "after_rollback"]
