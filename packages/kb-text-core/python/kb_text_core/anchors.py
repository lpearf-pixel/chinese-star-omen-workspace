from __future__ import annotations

import re

from .models import AnchorContext


PAGE_MARKER_RE = re.compile(r"<pb:([^>]+)>")
MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def nearest_page_marker(text: str, offset: int) -> str | None:
    marker: str | None = None
    for match in PAGE_MARKER_RE.finditer(text, 0, max(offset, 0) + 1):
        marker = match.group(1)
    return marker


def _indent_width(raw_line: str) -> int:
    width = 0
    for ch in raw_line:
        if ch == " ":
            width += 1
        elif ch == "\t":
            width += 4
        elif ch == "　":
            width += 2
        else:
            break
    return width


def _is_ancient_heading(raw_line: str) -> bool:
    stripped = raw_line.strip()
    if not stripped or stripped.startswith("<pb:") or stripped.startswith("#"):
        return False
    if _indent_width(raw_line) < 2 or len(stripped) > 32:
        return False
    if "曰" in stripped or stripped.endswith("撰"):
        return False
    if any(ch in stripped for ch in "。；，,：:()（）/[]【】"):
        return False
    if re.search(r"[A-Za-z0-9]", stripped):
        return False
    if any(token in stripped for token in ("故", "而", "者", "其", "之", "也")) and not stripped.endswith(
        ("占", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十")
    ):
        return False
    return True


def heading_ranges(text: str) -> list[tuple[int, int, str, int]]:
    ranges: list[tuple[int, int, str, int]] = []
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        markdown = MARKDOWN_HEADING_RE.match(line)
        if markdown:
            ranges.append((offset, offset + len(line), markdown.group(2).strip(), len(markdown.group(1))))
        elif _is_ancient_heading(line):
            ranges.append((offset, offset + len(line), line.strip(), 10 + _indent_width(line)))
        offset += len(raw_line)
    return ranges


def span_is_heading(text: str, start: int, end: int) -> bool:
    return any(start >= left and end <= right for left, right, _, _ in heading_ranges(text))


def heading_path_at(text: str, offset: int) -> list[str]:
    markdown: dict[int, str] = {}
    ancient: dict[int, str] = {}
    for left, _, heading, level in heading_ranges(text):
        if left > max(offset, 0):
            break
        if level <= 6:
            markdown[level] = heading
            for existing in list(markdown):
                if existing > level:
                    markdown.pop(existing, None)
            ancient.clear()
        else:
            indent_level = level - 10
            ancient[indent_level] = heading
            for existing in list(ancient):
                if existing > indent_level:
                    ancient.pop(existing, None)

    path = [markdown[level] for level in sorted(markdown)]
    for level in sorted(ancient):
        value = ancient[level]
        if not path or path[-1] != value:
            path.append(value)
    return path


def paragraph_index_at(text: str, offset: int) -> int:
    prefix = text[: max(offset, 0)]
    blocks = [block for block in re.split(r"\n\s*\n", prefix) if block.strip()]
    return max(len(blocks) - 1, 0)


def extract_anchor(text: str, start: int, end: int, *, window: int = 180) -> str:
    requested_left = max(0, start - window)
    requested_right = min(len(text), end + window)

    line_left = text.rfind("\n", 0, requested_left)
    left = line_left + 1 if line_left >= 0 else requested_left
    line_right = text.find("\n", requested_right)
    right = line_right if line_right >= 0 else requested_right

    blank_left = text.rfind("\n\n", max(0, start - window * 2), start)
    if blank_left >= 0 and blank_left + 2 > left:
        left = blank_left + 2
    blank_right = text.find("\n\n", end, min(len(text), end + window * 2))
    if blank_right >= 0 and blank_right < right:
        right = blank_right

    return re.sub(r"[\t\r\n]+", " ", text[left:right].strip())


def build_anchor_context(text: str, start: int, end: int, *, window: int = 180) -> AnchorContext:
    return AnchorContext(
        page_marker=nearest_page_marker(text, start),
        heading_path=heading_path_at(text, start),
        paragraph_index=paragraph_index_at(text, start),
        anchor_text=extract_anchor(text, start, end, window=window),
    )
