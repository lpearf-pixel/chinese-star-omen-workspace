"""Normalize stellar queries before embedding while preserving the raw query option."""

from __future__ import annotations

from typing import List, Optional

from . import config

REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("荧惑守心", "熒惑守心"),
    ("荧惑", "熒惑"),
)

_opencc_converter: Optional[object] = None
_opencc_init_failed = False


def _opencc_disabled_name(name: str) -> bool:
    return name.strip().lower() in ("", "none", "off", "disabled", "0", "false", "no")


def _get_opencc():
    global _opencc_converter, _opencc_init_failed
    cfg = config.KB_OPENCC_CONFIG
    if _opencc_disabled_name(cfg) or _opencc_init_failed:
        return None
    if _opencc_converter is None:
        try:
            from opencc import OpenCC

            _opencc_converter = OpenCC(cfg)
        except Exception:
            _opencc_init_failed = True
            return None
    return _opencc_converter


def _apply_opencc(text: str) -> str:
    converter = _get_opencc()
    return text if converter is None else converter.convert(text)


def _apply_seed_replacements(text: str) -> str:
    output = text
    for source, target in REPLACEMENTS:
        output = output.replace(source, target)
    return output


def normalize_stellar_query(text: str) -> str:
    if not config.KB_QUERY_STELLAR_NORMALIZE:
        return text or ""
    normalized = _apply_opencc((text or "").strip())
    return _apply_seed_replacements(normalized)


def iter_embedding_query_strings(text: str) -> List[str]:
    raw = (text or "").strip()
    if not config.KB_QUERY_STELLAR_NORMALIZE:
        return [raw] if raw else [""]
    normalized = _apply_seed_replacements(_apply_opencc(raw))
    if not config.KB_QUERY_DUAL_SCRIPT or normalized == raw:
        return [normalized] if normalized else [""]
    return [normalized, raw]
