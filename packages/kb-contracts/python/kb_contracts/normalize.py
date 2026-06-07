from __future__ import annotations

import re

_PINYIN_OVERRIDES = {
    "荧惑守心": "yinghuo_shouxin",
    "熒惑守心": "yinghuo_shouxin",
    "荧惑 守心": "yinghuo_shouxin",
    "熒惑 守心": "yinghuo_shouxin",
}
_TRADITIONAL_TO_SIMPLIFIED = str.maketrans({"熒": "荧", "併": "并"})


def normalize_term(term: str) -> str:
    """Return a stable ASCII-ish slug for IDs, with known Chinese omen overrides."""
    compact = "".join(str(term or "").strip().split()).translate(_TRADITIONAL_TO_SIMPLIFIED)
    if compact in _PINYIN_OVERRIDES:
        return _PINYIN_OVERRIDES[compact]
    lowered = compact.lower()
    lowered = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered or "unknown"
