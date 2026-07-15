from __future__ import annotations

from .models import NormalizedText


SIMPLIFIED_MAP = str.maketrans(
    {
        "熒": "荧",
        "併": "并",
        "臺": "台",
        "裏": "里",
    }
)
TRADITIONAL_MAP = str.maketrans(
    {
        "荧": "熒",
        "并": "併",
        "台": "臺",
        "里": "裏",
    }
)


def canonicalize_char(ch: str) -> str:
    return ch.translate(SIMPLIFIED_MAP)


def normalize_search_text(text: str) -> str:
    return "".join(canonicalize_char(ch) for ch in str(text or "") if not ch.isspace())


def compact_with_index_map(text: str) -> NormalizedText:
    chars: list[str] = []
    index_map: list[int] = []
    for idx, ch in enumerate(str(text or "")):
        if ch.isspace():
            continue
        chars.append(canonicalize_char(ch))
        index_map.append(idx)
    return NormalizedText(compact="".join(chars), index_map=index_map)


def query_variants(query: str) -> list[str]:
    raw = str(query or "").strip()
    compact = "".join(raw.split())
    simplified = compact.translate(SIMPLIFIED_MAP)
    traditional = compact.translate(TRADITIONAL_MAP)
    values = [raw, compact, simplified, traditional]
    if len(compact) > 2:
        values.extend(
            [
                f"{compact[:2]} {compact[2:]}",
                f"{simplified[:2]} {simplified[2:]}",
                f"{traditional[:2]} {traditional[2:]}",
            ]
        )
    out: list[str] = []
    for value in values:
        if value and value not in out:
            out.append(value)
    return out


def normalized_query_variants(query: str, variants: list[str] | None = None) -> list[str]:
    out: list[str] = []
    for value in variants or query_variants(query):
        normalized = normalize_search_text(value)
        if normalized and normalized not in out:
            out.append(normalized)
    return out


def split_loose_terms(query: str) -> list[str]:
    compact = normalize_search_text(query)
    if not compact:
        return []

    bodies = ["荧惑", "太白", "填星", "岁星", "辰星", "日", "月", "五星"]
    actions = ["守", "犯", "入", "合", "聚", "逆", "留", "贯", "乘", "食", "蚀"]

    terms: list[str] = []
    remainder = compact
    for body in bodies:
        if compact.startswith(body):
            terms.append(body)
            remainder = compact[len(body):]
            break

    for action in actions:
        if action in remainder:
            before, after = remainder.split(action, 1)
            if before:
                terms.append(before)
            terms.append(action)
            if after:
                terms.append(after)
            break
    else:
        if remainder:
            terms.append(remainder)

    return [term for idx, term in enumerate(terms) if term and term not in terms[:idx]]
