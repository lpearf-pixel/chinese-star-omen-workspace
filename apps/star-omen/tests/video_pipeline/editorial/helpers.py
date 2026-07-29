from __future__ import annotations

import json
from pathlib import Path

from src.video_pipeline.asterisms import load_asterism_catalog
from src.video_pipeline.contracts import AstronomyEventV1
from src.video_pipeline.rule_assessment import build_rule_assessment_result

APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parents[1]
TEMPLATE_PATH = (
    APP_ROOT
    / "data"
    / "video_pipeline"
    / "templates"
    / "zh_cn_vertical_slice_v1.yaml"
)
CATALOG_PATH = APP_ROOT / "data" / "video_pipeline" / "asterism_catalog_v1.yaml"
EVIDENCE_ROOT = WORKSPACE_ROOT / "tests" / "fixtures" / "evidence" / "v1"


def july_inputs():
    event = AstronomyEventV1.model_validate_json(
        (EVIDENCE_ROOT / "july-21-event.json").read_text(encoding="utf-8")
    )
    assessment_result = build_rule_assessment_result(
        event=event,
        rules=[],
        rule_set_version="rules:empty-v1",
        kb_root=EVIDENCE_ROOT / "kb-root",
    )
    mapping = load_asterism_catalog(CATALOG_PATH).catalog.resolve("spica")
    return event, assessment_result, mapping


def evidence_rich_inputs():
    event = AstronomyEventV1.model_validate_json(
        (EVIDENCE_ROOT / "evidence-rich-event.json").read_text(encoding="utf-8")
    )
    rules = json.loads(
        (EVIDENCE_ROOT / "evidence-rich-rules.json").read_text(encoding="utf-8")
    )
    result = build_rule_assessment_result(
        event=event,
        rules=rules,
        rule_set_version="rules:evidence-rich-v1",
        kb_root=EVIDENCE_ROOT / "kb-root",
    )
    return event, result


def modern_asset_payload(text: str | None = None) -> dict:
    return {
        "asset_id": "interpretation:open-mouth-v1",
        "text": text
        or "现代文化转译：把‘开口破局’理解为主动表达与澄清问题的提醒。",
        "disclosure": "现代文化转译",
        "review_status": "approved",
    }


def historical_asset_payload(text: str | None = None) -> dict:
    return {
        "asset_id": "history:traditional-asterism-context-v1",
        "text": text or "角宿属于传统中国星官体系，现代天文学使用恒星目录进行对应。",
        "source_title": "Chinese sky-culture catalog context",
        "source_type": "catalog_context",
        "review_status": "approved",
    }


def stellarium_capability_payload() -> dict:
    return {
        "schema_version": "stellarium-capability/v1",
        "stellarium_version": "26.2.0",
        "api_series": "26.x",
        "commands": [
            "core.clear",
            "core.setGuiVisible",
            "core.setDate",
            "core.setTimeRate",
            "core.setObserverLocation",
            "core.selectObjectByName",
            "core.wait",
            "StelMovementMgr.setFlagTracking",
            "StelMovementMgr.zoomTo",
        ],
    }
