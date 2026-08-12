from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.video_pipeline.contracts import (
    ExternalAuditBundleV1,
    ExternalMediaSourceV1,
)


APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parents[1]
DATA_ROOT = (
    APP_ROOT
    / "data"
    / "video_pipeline"
    / "external_media"
    / "祖山觀"
)
SOURCE_SET_PATH = DATA_ROOT / "source-set-v1.json"
WMO_SNAPSHOT_PATH = (
    DATA_ROOT / "evidence" / "wmo-tropical-cyclone-characteristics.json"
)
FIXTURE_MANIFEST_PATH = (
    WORKSPACE_ROOT
    / "tests"
    / "fixtures"
    / "external-media"
    / "祖山觀"
    / "manifest.json"
)

CREATOR_SEC_UID = (
    "MS4wLjABAAAAAzgxglR-dz-mRK53rZNuTqMwh1HktiIHLXa-"
    "3ZSVXCH4zDH0xjcWCN8BKyQ3plyK"
)
PRIORITY_EPISODES = [1, 2, 3, 7, 9, 11, 16, 20, 22]
GOLD_EPISODE = 22
GOLD_WORK_ID = "7669807398794598565"
EXPECTED_SOURCE_INVENTORY = [
    (
        1,
        "7664842500762644581",
        "note",
        "2026-07-21T05:03:33Z",
        "bd1b800b1d96e01708cce2b0bef068e18dcef4653eb93fc11da00a912f6bc531",
    ),
    (
        2,
        "7664936677178591483",
        "video",
        "2026-07-21T11:09:00Z",
        "3c5948726d40acb3b9821a967be3d432a73f6058158af5085b8c8ce4c4816cbe",
    ),
    (
        3,
        "7665347263846490225",
        "note",
        "2026-07-22T13:42:17Z",
        "7d94e5f64e63eb35ad5ef23377f3d58db82762f0858715283e0bd543e8a73256",
    ),
    (
        4,
        "7665915757523717489",
        "note",
        "2026-07-24T02:28:21Z",
        "c406f142056acda001383e052a308706a38416f25df9a9dc507f077191f43316",
    ),
    (
        5,
        "7666397658521691633",
        "video",
        "2026-07-25T09:38:21Z",
        "d08455ca4d2c1f5a2222e6f1addada454b82aadf240a45cf60e85eccbcb353d3",
    ),
    (
        6,
        "7666456983474315185",
        "note",
        "2026-07-25T13:28:34Z",
        "77c406cf25010b92c386ef9dcecfcb585847b6a304a245fde9bfaa687346e234",
    ),
    (
        7,
        "7666798804096819897",
        "note",
        "2026-07-26T11:35:00Z",
        "35a8b0b6cd480a0438a2b20f820fbbd0c32b8c91f6a9f3b74ea1d91e3045c805",
    ),
    (
        8,
        "7667150802499713969",
        "note",
        "2026-07-27T10:20:56Z",
        "9225be0b63e174ae9682370779618f87d357801ce16722d129b12fcf0f3b87a4",
    ),
    (
        9,
        "7667518986020752762",
        "video",
        "2026-07-28T10:09:41Z",
        "0d756fbeccbe59322a03131c840131453407e5f9713f36a12d5e4438c3bced04",
    ),
    (
        10,
        "7667861767431682033",
        "note",
        "2026-07-29T08:19:51Z",
        "95c0a6aa195bc1d4e867606b2fe2869c833e0261130c1d5571ea740cffde11fe",
    ),
    (
        11,
        "7667900213386545009",
        "video",
        "2026-07-29T10:49:03Z",
        "5781ac777e160188fd5ca1772ae381492b280b6a07feb71e84eda6d38cace6bd",
    ),
    (
        12,
        "7668286758269765617",
        "note",
        "2026-07-30T11:49:02Z",
        "499fd4934a1992b08d74364ca571a972090473497dbaf708aac1c78f4b0dc094",
    ),
    (
        13,
        "7668504981377007281",
        "note",
        "2026-07-31T01:55:51Z",
        "d1e2c820aa8000a2ea0659326e698cc0c9c41efa79d873bcb189f2dc62e64a44",
    ),
    (
        14,
        "7668704693770518513",
        "note",
        "2026-07-31T14:50:50Z",
        "9bde3e221d0fafcb45961a32698137fecb8cfbc35cf4a76f558639c7ef140d17",
    ),
    (
        15,
        "7668878719603831473",
        "note",
        "2026-08-01T02:06:09Z",
        "23ea41f3df11742a1107d48417c35ddfdebecdb34ccbddc7794213ca9c7f3570",
    ),
    (
        16,
        "7669012449136450673",
        "video",
        "2026-08-01T10:45:05Z",
        "7401f70281894f42983a47455a7e78790b0ab9712f1b21cdaa1372427a177d28",
    ),
    (
        17,
        "7669032260142594481",
        "note",
        "2026-08-01T12:01:57Z",
        "75b970a60dd40edb7a6d21fe898589d64154c924de71e5ff6304accd7d17c132",
    ),
    (
        18,
        "7669229974720724581",
        "note",
        "2026-08-02T00:49:12Z",
        "17f951b6a4685d7fc6fc67d940bc24aa9d787528a6f6ef9f578f7d48830fdb68",
    ),
    (
        19,
        "7669273330567188849",
        "note",
        "2026-08-02T03:37:26Z",
        "8aeab1405ab1ceface3846537a1552e68ca353b4054cb5e9e2ab4c87ccfd0601",
    ),
    (
        20,
        "7669445710950025073",
        "note",
        "2026-08-02T14:46:22Z",
        "8a89bb5b61de32881d5e9cd03d8eed21fb6f5d1d80869a1d7bf77f182cbde927",
    ),
    (
        21,
        "7669770178008439418",
        "video",
        "2026-08-03T11:45:27Z",
        "d11e032ef9eaad3d541ca3b096cd6222c64a0b7e9d17ec743660604c566dac9d",
    ),
    (
        22,
        "7669807398794598565",
        "note",
        "2026-08-03T14:09:54Z",
        "2623af26940be8c89a29e644ba5e8d819956ee5afffca1d9fe3dc22d6c0d95f4",
    ),
    (
        23,
        "7670049464699455217",
        "note",
        "2026-08-04T05:49:14Z",
        "b300e1e97cb802d7ed535a82e93657f01d22c621c32ca61a7b5fb60a3789a33c",
    ),
]


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


def load_source_set() -> dict:
    raw = SOURCE_SET_PATH.read_bytes()
    payload = json.loads(raw)
    assert raw == canonical_json_bytes(payload)
    return payload


def load_fixture_manifest() -> dict:
    raw = FIXTURE_MANIFEST_PATH.read_bytes()
    payload = json.loads(raw)
    assert raw == canonical_json_bytes(payload)
    return payload


def audit_assets() -> list[tuple[dict, bytes, dict]]:
    manifest = load_fixture_manifest()
    assets: list[tuple[dict, bytes, dict]] = []
    for entry in manifest["assets"]:
        if entry["asset_kind"] != "audit_bundle":
            continue
        path = WORKSPACE_ROOT / entry["path"]
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
        payload = json.loads(raw)
        assert raw == canonical_json_bytes(payload)
        assets.append((entry, raw, payload))
    return assets


def test_source_set_freezes_exact_creator_collection_and_denominator() -> None:
    payload = load_source_set()

    assert payload["schema_version"] == "external-media-source-set/v1"
    assert payload["creator"] == {
        "display_name": "祖山觀（無用之人）🌓",
        "douyin_number": "35031221639",
        "platform_uid": "2129076815950670",
        "profile_url": f"https://www.douyin.com/user/{CREATOR_SEC_UID}",
        "sec_uid": CREATOR_SEC_UID,
    }
    assert payload["collection"] == {
        "collection_id": "7664842437629921326",
        "collection_url": "https://www.douyin.com/collection/7664842437629921326/1",
        "display_name": "8月必看天象值得期待",
        "approved_episode_denominator": 23,
        "captured_live_total_episode": 40,
        "included_episode_numbers": list(range(1, 24)),
        "excluded_source_drift_episode_numbers": list(range(24, 41)),
    }
    assert payload["selection"] == {
        "gold_episode": GOLD_EPISODE,
        "priority_episode_numbers": PRIORITY_EPISODES,
        "rubric_id": "high-risk-caption-claims/v1",
        "rubric_note": (
            "Prioritize captions with rarity, classical/historical authority, "
            "astronomical relation, or weather/climate inference claims."
        ),
    }
    assert payload["capture_scope"] == "public_metadata_only"
    assert payload["review_status"] == "candidate"
    assert payload["reviewer_id"] is None
    assert payload["source_gate_evidence"]["resolved_direct_work_id"] == (
        "7673054975425692773"
    )
    assert payload["source_gate_evidence"][
        "resolved_direct_work_published_at_utc"
    ] == "2026-08-12T08:12:10Z"

    items = payload["source_items"]
    assert len(items) == 23
    assert [item["episode_number"] for item in items] == list(range(1, 24))
    assert len({item["source"]["platform_work_id"] for item in items}) == 23
    assert [
        (
            item["episode_number"],
            item["source"]["platform_work_id"],
            item["platform_observation"]["media_kind"],
            item["source"]["published_at_utc"],
            item["source"]["captures"][0]["content_sha256"],
        )
        for item in items
    ] == EXPECTED_SOURCE_INVENTORY
    for episode, work_id, media_kind, _, _ in EXPECTED_SOURCE_INVENTORY:
        assert items[episode - 1]["source"]["fixed_url"] == (
            f"https://www.douyin.com/{media_kind}/{work_id}"
        )


def test_every_source_validates_and_binds_exact_description_hash() -> None:
    payload = load_source_set()

    note_count = 0
    video_count = 0
    for item in payload["source_items"]:
        episode = item["episode_number"]
        source = ExternalMediaSourceV1.model_validate(item["source"])
        observation = item["platform_observation"]
        description = item["captured_description"]
        digest = hashlib.sha256(description.encode("utf-8")).hexdigest()
        capture = source.captures[0]

        assert source.source_id == (
            f"media:douyin:zushan:collection-7664842437629921326:episode-{episode:02d}"
        )
        assert source.creator_id == "creator:douyin:2129076815950670"
        assert source.creator_account_locator == CREATOR_SEC_UID
        assert source.creator_display_name == "祖山觀（無用之人）🌓"
        assert source.capture_status == "metadata_only"
        assert len(source.captures) == 1
        assert capture.capture_type == "description"
        assert capture.content_sha256 == digest
        assert capture.content_locator == f"{source.fixed_url}#description"
        assert capture.rights_status == "metadata_only"
        assert str(source.published_at_utc).endswith("+00:00")

        work_id = source.platform_work_id
        if observation["media_kind"] == "note":
            note_count += 1
            assert observation["aweme_type"] == 68
            assert observation["image_uris"]
            assert observation["video_uri"] is None
            assert str(source.fixed_url) == f"https://www.douyin.com/note/{work_id}"
        else:
            video_count += 1
            assert observation["media_kind"] == "video"
            assert observation["aweme_type"] == 0
            assert observation["image_uris"] == []
            assert observation["video_uri"]
            assert str(source.fixed_url) == f"https://www.douyin.com/video/{work_id}"

    assert (note_count, video_count) == (17, 6)


def test_fixture_manifest_binds_every_real_asset() -> None:
    manifest = load_fixture_manifest()

    assert manifest["schema_version"] == "external-media-real-asset-manifest/v1"
    assert manifest["creator_id"] == "creator:douyin:2129076815950670"
    assert manifest["collection_id"] == "7664842437629921326"
    assert manifest["real_source_warning"] == (
        "Research lead only; never classical evidence or rule authority."
    )
    assert len(manifest["assets"]) == 11
    assert len(
        [item for item in manifest["assets"] if item["asset_kind"] == "audit_bundle"]
    ) == 9

    for entry in manifest["assets"]:
        path = WORKSPACE_ROOT / entry["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]


def test_nine_priority_audits_are_closed_candidate_bundles() -> None:
    source_set = load_source_set()
    source_by_episode = {
        item["episode_number"]: item for item in source_set["source_items"]
    }
    assets = audit_assets()

    assert [entry["episode_number"] for entry, _, _ in assets] == PRIORITY_EPISODES
    for entry, _, payload in assets:
        episode = entry["episode_number"]
        bundle = ExternalAuditBundleV1.model_validate(payload)
        expected_source = source_by_episode[episode]["source"]
        captured_text = source_by_episode[episode]["captured_description"]

        assert bundle.source.model_dump(mode="json") == ExternalMediaSourceV1.model_validate(
            expected_source
        ).model_dump(mode="json")
        assert bundle.audit.review_status == "candidate"
        assert bundle.audit.reviewer_id is None
        assert bundle.audit.research_only is True
        assert bundle.audit.grants_rule_authority is False
        assert bundle.audit.grants_classical_authority is False
        assert all(claim.review_status == "candidate" for claim in bundle.claims)
        assert all(claim.reviewer_id is None for claim in bundle.claims)
        assert all(link.review_status == "candidate" for link in bundle.evidence_links)
        assert all(link.reviewer_id is None for link in bundle.evidence_links)

        for claim in bundle.claims:
            span = claim.source_span
            start = int(span.start_offset)
            end = int(span.end_offset)
            assert span.offset_unit == "unicode_codepoints"
            assert span.exact_text == captured_text[start:end]
            assert span.capture_sha256 == hashlib.sha256(
                captured_text.encode("utf-8")
            ).hexdigest()


def test_bi_gale_gold_sample_is_complete_without_weather_equivalence() -> None:
    assets = audit_assets()
    _, _, payload = next(
        asset for asset in assets if asset[0]["episode_number"] == GOLD_EPISODE
    )
    bundle = ExternalAuditBundleV1.model_validate(payload)

    assert bundle.source.platform_work_id == GOLD_WORK_ID
    assert str(bundle.source.fixed_url) == f"https://www.douyin.com/note/{GOLD_WORK_ID}"
    assert [claim.source_span.exact_text for claim in bundle.claims] == [
        "毕宿天象的烈风",
        "能不能对应海上风暴？",
    ]
    assert [claim.claim_class for claim in bundle.claims] == [
        "historical_correspondence",
        "modern_inference",
    ]
    assessments = {item.claim_id: item for item in bundle.audit.assessments}
    first, second = bundle.claims
    assert assessments[first.claim_id].disposition == "source_missing"
    assert assessments[first.claim_id].evidence_link_ids == []
    assert assessments[second.claim_id].disposition == "ambiguous"
    assert bundle.audit.overall_disposition == "ambiguous"
    assert len(bundle.evidence_links) == 1
    assert bundle.evidence_links[0].evidence_class == "modern_authority"
    assert bundle.evidence_links[0].relationship == "context_only"
    assert str(bundle.evidence_links[0].evidence_locator) == (
        "https://wmo.int/content/characteristics-of-tropical-cyclones"
    )
    snapshot_raw = WMO_SNAPSHOT_PATH.read_bytes()
    snapshot = json.loads(snapshot_raw)
    assert snapshot_raw == canonical_json_bytes(snapshot)
    evidence_link = bundle.evidence_links[0]
    assert evidence_link.evidence_ref_id == snapshot["evidence_ref_id"]
    assert str(evidence_link.evidence_locator) == snapshot["source_url"]
    assert evidence_link.evidence_sha256 == hashlib.sha256(snapshot_raw).hexdigest()
    rationale = " ".join(item.rationale for item in bundle.audit.assessments)
    assert "does not establish equivalence" in rationale
    assert not any(
        item.disposition in {"supported_exact", "modern_inference_only"}
        for item in bundle.audit.assessments
    )
