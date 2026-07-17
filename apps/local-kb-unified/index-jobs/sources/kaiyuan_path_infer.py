"""Infer conservative Kaiyuan metadata when Markdown frontmatter is absent."""

from __future__ import annotations

import os
from typing import Any, Dict


def infer_enabled() -> bool:
    return os.environ.get("KB_KAIYUAN_METADATA_INFER", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _normalize(relative_path: str) -> str:
    return relative_path.replace("\\", "/").strip()


def _in_kaiyuan_tree(value: str) -> bool:
    return "唐開元占經" in value or "開元占經" in value


def _layer_defaults(value: str) -> Dict[str, Any]:
    wrapped = f"/{value}/"
    if "问答样例" in value:
        return {"card_type": "qa_example", "evidence_level": "example", "final_citable": False, "query_mode_hint": "workflow_only"}
    if (
        "/agent/" in wrapped
        or value.startswith("agent/")
        or "/prompts/" in wrapped
        or value.startswith("prompts/")
        or "02-Agent入口" in value
        or value.endswith("schema.yaml")
    ):
        return {"card_type": "prompt_asset", "evidence_level": "prompt", "final_citable": False, "query_mode_hint": "workflow_only"}
    if "/分卷/" in wrapped:
        return {"card_type": "fenjuan", "evidence_level": "primary", "final_citable": True, "query_mode_hint": "evidence"}
    if "全文合并版" in value or "全文合併版" in value:
        return {"card_type": "fulltext", "evidence_level": "primary", "final_citable": True, "query_mode_hint": "evidence"}
    if "/星官卡/" in wrapped:
        return {"card_type": "xingguan_card", "evidence_level": "structured", "final_citable": False, "query_mode_hint": "entity"}
    if "/逐宿卡/" in wrapped:
        return {"card_type": "zhusu_card", "evidence_level": "structured", "final_citable": False, "query_mode_hint": "entity"}
    if "/术语卡片/" in wrapped:
        return {"card_type": "term_card", "evidence_level": "structured", "final_citable": False, "query_mode_hint": "entity"}
    if "/知识抽取卡/" in wrapped:
        return {"card_type": "extract_card", "evidence_level": "structured", "final_citable": False, "query_mode_hint": "entity"}
    if "/主题索引/" in wrapped:
        return {"card_type": "topic_index", "evidence_level": "index", "final_citable": False, "query_mode_hint": "support"}
    if "/章节摘要卡/" in wrapped:
        return {"card_type": "chapter_summary", "evidence_level": "index", "final_citable": False, "query_mode_hint": "support"}
    if "/导航/" in wrapped:
        return {"card_type": "nav", "evidence_level": "index", "final_citable": False, "query_mode_hint": "support"}
    return {}


def path_defaults(relative_path: str) -> Dict[str, Any]:
    normalized = _normalize(relative_path)
    if not normalized or not _in_kaiyuan_tree(normalized):
        return {}
    return {
        "kb_book_id": "kaiyuan_zhanjing",
        "book_title": "唐開元占經",
        **_layer_defaults(normalized),
    }


def merge_fm_with_path_defaults(relative_path: str, frontmatter: Dict[str, Any]) -> Dict[str, Any]:
    if not infer_enabled():
        return dict(frontmatter)
    defaults = path_defaults(relative_path)
    return {**defaults, **frontmatter} if defaults else dict(frontmatter)
