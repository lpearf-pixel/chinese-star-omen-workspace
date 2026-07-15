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


def _is_ancient_heading(raw_line: str) -> bool:
    stripped = raw_line.strip()
    if not stripped or stripped.startswith("<pb:") or stripped.startswith("#"):
        return False
    leading = len(raw_line) - len(raw_line.lstrip(" \t　"))
    if leading < 2 or len(stripped) > 40:
        return False
    if "曰" in stripped or any(ch in stripped for ch in "。；，,()（）/"):
        return False
    return True


def heading_path_at(text: str, offset: int) -> list[str]:
    markdown: dict[int, str] = {}
    ancient: str | None = None
    position = 0
    for raw_line in text[: max(offset, 0)].splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        match = MARKDOWN_HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            markdown[level] = match.group(2).strip()
            for existing in list(markdown):
                if existing > level:
                    markdown.pop(existing, None)
            ancient = None
        elif _is_ancient_heading(line):
            ancient = line.strip()
        position += len(raw_line)
        if position >= offset:
            break

    path = [markdown[level] for level in sorted(markdown)]
    if ancient and (not path or ancient != path[-1]):
        path.append(ancient)
    return path


def paragraph_index_at(text: str, offset: int) -> int:
    prefix = text[: max(offset, 0)]
    blocks = [block for block in re.split(r"\n\s*\n", prefix) if block.strip()]
    return max(len(blocks) - 1, 0)


def extract_anchor(text: str, start: int, end: int, *, window: int = 160) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)

    line_left = text.rfind("\n", left, start)
    if line_left >= 0:
        left = line_left + 1
    line_right = text.find("\n", end, right)
    if line_right >= 0:
        right = line_right

    return " ".join(text[left:right].split())


def build_anchor_context(text: str, start: int, end: int, *, window: int = 160) -> AnchorContext:
    return AnchorContext(
        page_marker=nearest_page_marker(text, start),
        heading_path=heading_path_at(text, start),
        paragraph_index=paragraph_index_at(text, start),
        anchor_text=extract_anchor(text, start, end, window=window),
    )
