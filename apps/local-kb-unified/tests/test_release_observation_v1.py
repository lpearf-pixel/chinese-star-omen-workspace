from __future__ import annotations

import json

from release_observation import _config_hash, capture_phase_observation


STRUCTURED = [
    "xingguan_card",
    "zhusu_card",
    "term_card",
    "extract_card",
    "topic_index",
    "chapter_summary",
]
PRIMARY = ["fenjuan", "fulltext"]


def test_capture_builds_content_free_phase_from_read_only_adapters():
    calls = []

    def fetch_health():
        return {
            "http_status": 200,
            "body": {
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
                "default_collection": "local_kb_kaiyuan_v2",
            },
        }

    def fetch_meta():
        return {
            "http_status": 200,
            "body": {
                "meta_status": "ok",
                "schema_version": "corpus-manifest/v1",
                "corpus_version": "release",
                "ingest_run_id": "ingest_release",
                "source_manifest_hash": "sha256:source",
                "collection": "local_kb_kaiyuan_v2",
                "created_at": "2026-07-18T12:00:00Z",
                "managed_by": "local-kb-unified/v2",
                "collection_schema": "passage-v2",
            },
        }

    def retrieve(**request):
        calls.append(request)
        stage = request["retrieval_stage"]
        return {
            "http_status": 200,
            "body": {
                "retrieval_stage": stage,
                "card_types": request["card_types"],
                "collection": request["collection"],
                "retrieved_count": 1,
                "hits": [{"snippet": "SECRET SOURCE CONTENT", "path": "/private/source.md"}],
            },
        }

    def inspect_collection(collection):
        return {
            "exists": True,
            "points_count": 41 if collection == "local_kb_default" else 57,
            "config": {"vectors": {"size": 768, "distance": "Cosine"}, "shard_number": 1},
        }

    result = capture_phase_observation(
        active_collection="local_kb_kaiyuan_v2",
        query="熒惑守心",
        fetch_health=fetch_health,
        fetch_meta=fetch_meta,
        retrieve=retrieve,
        inspect_collection=inspect_collection,
        captured_at="2026-07-18T12:30:00Z",
    )

    assert result["schema_version"] == "kaiyuan-release-observation/v1"
    assert result["phase"]["active_collection"] == "local_kb_kaiyuan_v2"
    assert result["phase"]["smoke"]["structured_recall"]["card_types"] == STRUCTURED
    assert result["phase"]["smoke"]["primary_evidence"]["card_types"] == PRIMARY
    assert result["phase"]["collections"]["local_kb_default"]["points_count"] == 41
    assert result["phase"]["collections"]["local_kb_default"]["config_hash"].startswith("sha256:")
    assert [call["retrieval_stage"] for call in calls] == ["structured_recall", "primary_evidence"]
    assert all(call["filters"] == {"kb_book_id": "kaiyuan_zhanjing"} for call in calls)
    encoded = json.dumps(result, ensure_ascii=False, allow_nan=False)
    assert "SECRET SOURCE CONTENT" not in encoded
    assert "/private/source.md" not in encoded


def test_config_fingerprint_ignores_non_allowlisted_metadata():
    public = {
        "vectors": {"size": 768, "distance": "Cosine"},
        "shard_number": 1,
        "optimizer_config": {"indexing_threshold": 20000},
    }

    first = _config_hash({**public, "payload_sample": "SECRET-A", "internal_status": "green"})
    second = _config_hash({**public, "payload_sample": "SECRET-B", "internal_status": "yellow"})

    assert first == second
