from __future__ import annotations

from enum import Enum
from typing import Any


class CardType(str, Enum):
    FENJUAN = "fenjuan"
    FULLTEXT = "fulltext"
    XINGGUAN_CARD = "xingguan_card"
    ZHUSU_CARD = "zhusu_card"
    TERM_CARD = "term_card"
    EXTRACT_CARD = "extract_card"
    TOPIC_INDEX = "topic_index"
    CHAPTER_SUMMARY = "chapter_summary"
    NAV = "nav"
    PROMPT_ASSET = "prompt_asset"
    QA_EXAMPLE = "qa_example"


class EvidenceLevel(str, Enum):
    PRIMARY = "primary"
    STRUCTURED = "structured"
    INDEX = "index"
    PROMPT = "prompt"
    EXAMPLE = "example"


PROOF_PRIORITY: list[CardType] = [
    CardType.FENJUAN,
    CardType.FULLTEXT,
    CardType.XINGGUAN_CARD,
    CardType.ZHUSU_CARD,
    CardType.TERM_CARD,
    CardType.EXTRACT_CARD,
    CardType.TOPIC_INDEX,
    CardType.CHAPTER_SUMMARY,
    CardType.NAV,
    CardType.PROMPT_ASSET,
    CardType.QA_EXAMPLE,
]

FINAL_CITABLE_CARD_TYPES: set[CardType] = {
    CardType.FENJUAN,
    CardType.FULLTEXT,
}
NON_FACTUAL_CARD_TYPES: set[CardType] = {
    CardType.PROMPT_ASSET,
    CardType.QA_EXAMPLE,
}

STAGE1_RECALL_CARD_TYPES: list[CardType] = [
    CardType.XINGGUAN_CARD,
    CardType.ZHUSU_CARD,
    CardType.TERM_CARD,
    CardType.EXTRACT_CARD,
    CardType.TOPIC_INDEX,
    CardType.CHAPTER_SUMMARY,
]

STAGE2_PRIMARY_CARD_TYPES: list[CardType] = [
    CardType.FENJUAN,
    CardType.FULLTEXT,
]

CARD_TYPE_TO_EVIDENCE_LEVEL: dict[CardType, EvidenceLevel] = {
    CardType.FENJUAN: EvidenceLevel.PRIMARY,
    CardType.FULLTEXT: EvidenceLevel.PRIMARY,
    CardType.XINGGUAN_CARD: EvidenceLevel.STRUCTURED,
    CardType.ZHUSU_CARD: EvidenceLevel.STRUCTURED,
    CardType.TERM_CARD: EvidenceLevel.STRUCTURED,
    CardType.EXTRACT_CARD: EvidenceLevel.STRUCTURED,
    CardType.TOPIC_INDEX: EvidenceLevel.INDEX,
    CardType.CHAPTER_SUMMARY: EvidenceLevel.INDEX,
    CardType.NAV: EvidenceLevel.INDEX,
    CardType.PROMPT_ASSET: EvidenceLevel.PROMPT,
    CardType.QA_EXAMPLE: EvidenceLevel.EXAMPLE,
}

PATH_CARD_TYPE_RULES: list[tuple[str, str]] = [
    ("/分卷/", CardType.FENJUAN.value),
    ("全文合併版", CardType.FULLTEXT.value),
    ("全文合并版", CardType.FULLTEXT.value),
    ("/星官卡/", CardType.XINGGUAN_CARD.value),
    ("/逐宿卡/", CardType.ZHUSU_CARD.value),
    ("/术语卡片/", CardType.TERM_CARD.value),
    ("/知识抽取卡/", CardType.EXTRACT_CARD.value),
    ("/主题索引/", CardType.TOPIC_INDEX.value),
    ("/章节摘要卡/", CardType.CHAPTER_SUMMARY.value),
    ("/导航/", CardType.NAV.value),
    ("/agent/", CardType.PROMPT_ASSET.value),
    ("/prompts/", CardType.PROMPT_ASSET.value),
    ("02-Agent入口.md", CardType.PROMPT_ASSET.value),
    ("schema.yaml", CardType.PROMPT_ASSET.value),
    ("/问答样例库/", CardType.QA_EXAMPLE.value),
]

BOOK_TITLE_TO_ID: dict[str, str] = {
    "唐開元占經": "kaiyuan_zhanjing",
    "唐开元占经": "kaiyuan_zhanjing",
    "開元占經": "kaiyuan_zhanjing",
    "开元占经": "kaiyuan_zhanjing",
}

CITABLE_VALIDATION_VERSION = "citable-evidence/v2"
CITABLE_REQUIRED_CHECKS = {
    "path",
    "card_type",
    "book",
    "locator",
    "page",
    "paragraph",
    "heading",
    "anchor",
    "hash",
}


def is_final_citable(card_type: str) -> bool:
    try:
        return CardType(card_type) in FINAL_CITABLE_CARD_TYPES
    except ValueError:
        return False


def resolve_evidence_level(card_type: str) -> str | None:
    try:
        return CARD_TYPE_TO_EVIDENCE_LEVEL[CardType(card_type)].value
    except ValueError:
        return None


def can_be_final_fact(card_type: str) -> bool:
    try:
        resolved = CardType(card_type)
    except ValueError:
        return False
    return (
        resolved in FINAL_CITABLE_CARD_TYPES
        and resolved not in NON_FACTUAL_CARD_TYPES
    )


def infer_book_title_from_path(path: str | None) -> str | None:
    if not path:
        return None
    normalized = path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    for index, token in enumerate(parts):
        if token == "古籍" and index + 1 < len(parts):
            return parts[index + 1]
    lowered = normalized.lower()
    if (
        "kaiyuanzhanjin" in lowered
        or "唐開元占經" in normalized
        or "唐开元占经" in normalized
    ):
        return "唐開元占經"
    return None


def infer_book_id_from_path(path: str | None) -> str | None:
    title = infer_book_title_from_path(path)
    if title:
        return BOOK_TITLE_TO_ID.get(title)
    return None


def infer_card_type_from_path(path: str | None) -> str | None:
    if not path:
        return None
    normalized = path.replace("\\", "/")
    for token, card_type in PATH_CARD_TYPE_RULES:
        if token in normalized:
            return card_type
    return None


def infer_metadata_from_path(path: str | None) -> dict[str, str | None]:
    card_type = infer_card_type_from_path(path)
    book_id = infer_book_id_from_path(path)
    return {
        "book_title": infer_book_title_from_path(path),
        "kb_book_id": book_id,
        "book_id": book_id,
        "card_type": card_type,
        "evidence_level": (
            resolve_evidence_level(card_type) if card_type else None
        ),
    }


def is_citable_evidence(evidence: dict[str, Any]) -> bool:
    """Return true only for source-verified passage evidence.

    A primary card label or an existing path alone is not sufficient.  The
    evidence resolver must have produced a complete v2 validation trace whose
    source, locator, page, passage, anchor and hashes all passed.
    """

    card_type = str(evidence.get("card_type") or "")
    if not can_be_final_fact(card_type):
        return False
    if evidence.get("status") != "citable":
        return False
    if evidence.get("final_citable") is not True:
        return False
    if not evidence.get("relative_path"):
        return False
    if evidence.get("path_exists") is not True:
        return False
    if not evidence.get("source_locator") or not evidence.get("page_marker"):
        return False
    if not evidence.get("anchor_text"):
        return False

    trace = evidence.get("trace")
    if not isinstance(trace, dict):
        return False
    if trace.get("validation_version") != CITABLE_VALIDATION_VERSION:
        return False
    checks = trace.get("checks")
    if not isinstance(checks, dict):
        return False
    if not CITABLE_REQUIRED_CHECKS.issubset(checks):
        return False
    if not all(checks.get(name) is True for name in CITABLE_REQUIRED_CHECKS):
        return False
    matched = trace.get("matched_passage")
    if not isinstance(matched, dict):
        return False
    return (
        matched.get("source_locator") == evidence.get("source_locator")
        and matched.get("page_marker") == evidence.get("page_marker")
        and matched.get("paragraph_index") == evidence.get("paragraph_index")
    )
