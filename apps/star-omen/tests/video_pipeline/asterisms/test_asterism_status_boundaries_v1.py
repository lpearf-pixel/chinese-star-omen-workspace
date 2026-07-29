from __future__ import annotations

from copy import deepcopy

from src.video_pipeline.asterisms import (
    AsterismCatalogV1,
    AsterismNarrationPolicy,
    AsterismStatus,
)


def source_payloads() -> list[dict]:
    return [
        {
            "source_id": "source:catalog-a",
            "source_type": "catalog-record",
            "title": "Catalog A",
            "revision": "2026-07-22",
            "path_or_record": "catalog/a",
            "content_hash_algorithm": "sha256",
            "content_hash": "a" * 64,
            "snapshot_path": "data/video_pipeline/sources/catalog-a.json",
            "locator": "record-a",
            "reference_frame": "ICRS J2000",
        },
        {
            "source_id": "source:catalog-b",
            "source_type": "catalog-record",
            "title": "Catalog B",
            "revision": "2026-07-22",
            "path_or_record": "catalog/b",
            "content_hash_algorithm": "sha256",
            "content_hash": "b" * 64,
            "snapshot_path": "data/video_pipeline/sources/catalog-b.json",
            "locator": "record-b",
            "reference_frame": "ICRS J2000",
        },
    ]


def entry_payload(
    *,
    object_id: str,
    status: str,
    method: str,
    confidence: float,
    aliases: list[str],
) -> dict:
    return {
        "modern_object_id": object_id,
        "traditional_star_id": f"traditional-{object_id.split(':')[-1]}",
        "asterism_id": "synthetic-asterism",
        "canonical_chinese_name": f"测试-{object_id}",
        "aliases": aliases,
        "catalog_epoch": "J2000",
        "reference_coordinates": {
            "frame": "icrs",
            "epoch": "J2000",
            "ra_deg": 10.0,
            "dec_deg": 10.0,
        },
        "source_refs": ["source:catalog-a", "source:catalog-b"],
        "mapping_method": method,
        "confidence": confidence,
        "editorial_status": status,
    }


def catalog_with_statuses() -> AsterismCatalogV1:
    return AsterismCatalogV1.model_validate(
        {
            "schema_version": "asterism-catalog/v1",
            "catalog_id": "synthetic-status-catalog-v1",
            "catalog_version": 1,
            "sources": source_payloads(),
            "entries": [
                entry_payload(
                    object_id="hip:10001",
                    status="verified_membership",
                    method="catalog-membership",
                    confidence=0.9,
                    aliases=["member-star"],
                ),
                entry_payload(
                    object_id="region:10002",
                    status="region_only",
                    method="region-definition",
                    confidence=0.6,
                    aliases=["region-star"],
                ),
                entry_payload(
                    object_id="hip:10003",
                    status="ambiguous",
                    method="catalog-membership",
                    confidence=0.5,
                    aliases=["ambiguous-star"],
                ),
            ],
        }
    )


def test_verified_membership_uses_membership_limited_narration() -> None:
    result = catalog_with_statuses().resolve("member-star")
    assert result.status is AsterismStatus.VERIFIED_MEMBERSHIP
    assert result.narration_policy is AsterismNarrationPolicy.EXPLICIT_MEMBERSHIP


def test_region_only_uses_region_limited_narration() -> None:
    result = catalog_with_statuses().resolve("region-star")
    assert result.status is AsterismStatus.REGION_ONLY
    assert result.narration_policy is AsterismNarrationPolicy.REGION_LIMITED


def test_ambiguous_mapping_is_blocked() -> None:
    result = catalog_with_statuses().resolve("ambiguous-star")
    assert result.status is AsterismStatus.AMBIGUOUS
    assert result.narration_policy is AsterismNarrationPolicy.BLOCKED


def test_unknown_query_is_unresolved_and_blocked() -> None:
    result = catalog_with_statuses().resolve("not-present")
    assert result.status is AsterismStatus.UNRESOLVED
    assert result.narration_policy is AsterismNarrationPolicy.BLOCKED
