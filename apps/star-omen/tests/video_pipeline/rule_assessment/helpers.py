from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kb_text_core import parse_kaiyuan_passages

from src.video_pipeline.contracts import AstronomyEventV1

RAW_PASSAGE = "石氏曰熒惑守心，天下兵起。"
PAGE_MARKER = "KR3g0018_WYG_031-17a"
LOCATOR = "KR3g0018_031"
RELATIVE_PATH = "古籍/唐開元占經/分卷/KR3g0018_031.md"


def source_text() -> str:
    return (
        "# 唐開元占經 卷31\n\n"
        "　熒惑占二\n"
        "　　熒惑犯東方七宿\n"
        "　　　熒惑犯心五\n"
        f"<pb:{PAGE_MARKER}>\n"
        f"{RAW_PASSAGE}\n\n"
        "甘氏曰熒惑守心，有急兵。\n"
    )


def write_citable_source(root: Path) -> dict[str, Any]:
    path = root / RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    text = source_text()
    path.write_text(text, encoding="utf-8")
    passage = parse_kaiyuan_passages(
        text,
        source_path=str(path),
        card_type="fenjuan",
    )[0]
    return {
        "kb_book_id": "kaiyuan_zhanjing",
        "book_title": "唐開元占經",
        "card_type": "fenjuan",
        "evidence_level": "primary",
        "relative_path": RELATIVE_PATH,
        "source_locator": LOCATOR,
        "source_volume": "卷31",
        "page_marker": PAGE_MARKER,
        "heading_path": list(passage.heading_path),
        "paragraph_index": passage.paragraph_index,
        "anchor_text": RAW_PASSAGE,
        "content_hash": passage.raw_content_hash,
        "raw_content_hash": passage.raw_content_hash,
        "normalized_content_hash": passage.normalized_content_hash,
    }


def valid_event() -> AstronomyEventV1:
    at = datetime(2026, 3, 11, 12, tzinfo=timezone.utc)
    return AstronomyEventV1.model_validate(
        {
            "schema_version": "astronomy-event/v1",
            "calculation_id": "calc:test:mars-guarding-xin",
            "event_id": "event:test:mars-guarding-xin",
            "event_type": "guarding",
            "primary_body": "mars",
            "target_body_or_region": "xin_xiu",
            "start_utc": at,
            "peak_utc": at,
            "end_utc": at,
            "observer": {
                "latitude_deg": 31.2304,
                "longitude_deg": 121.4737,
                "elevation_m": 4.0,
                "timezone": "Asia/Shanghai",
            },
            "measurements": [
                {
                    "measurement_id": "measurement:angular-distance",
                    "kind": "angular-distance-deg",
                    "value": 0.8,
                    "unit": "deg",
                    "reference_frame": "topocentric-apparent",
                },
                {
                    "measurement_id": "measurement:duration-days",
                    "kind": "duration-days",
                    "value": 4.0,
                    "unit": "day",
                    "reference_frame": "event-window",
                },
            ],
            "visibility": {
                "status": "visible",
                "target_altitude_deg": 25.0,
                "sun_altitude_deg": -18.0,
                "threshold_version": "visibility/v1",
            },
            "calculation_provenance": {
                "provider": "skyfield",
                "provider_version": "1.51",
                "ephemeris_id": "de421.bsp",
                "ephemeris_sha256": "a" * 64,
                "timescale_source": "skyfield-builtin",
            },
            "quality_status": "verified",
            "uncertainty_reasons": [],
        }
    )


def matching_rule(evidence: dict[str, Any] | None) -> dict[str, Any]:
    rule: dict[str, Any] = {
        "id": "rule:mars-guarding-xin:test-v1",
        "source_text": "熒惑守心",
        "source_book": "唐開元占經",
        "trigger": {
            "body": "mars",
            "event_type": "guarding",
            "target": "xin_xiu",
        },
        "effect_domain": ["politics"],
        "severity": "high",
        "time_window": "0-90d",
        "rule_priority": 10,
        "resolution_policy": "highest_score",
    }
    if evidence is not None:
        rule["evidence"] = deepcopy(evidence)
    return rule


def primary_hit(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        **deepcopy(evidence),
        "match_type": "exact_raw",
        "status": "official",
    }


class FakeRetriever:
    def __init__(self, result: dict[str, Any] | None = None, error: Exception | None = None):
        self.result = result or {
            "stage1": {"hits": []},
            "stage2": {
                "primary_candidates": [],
                "exact_hits": [],
                "candidate_overlay_hits": [],
                "structured_fallbacks": [],
                "official_primary_used": False,
                "fallback_used": False,
            },
        }
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def two_stage_retrieve(self, query: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"query": query, **kwargs})
        if self.error is not None:
            raise self.error
        return deepcopy(self.result)
