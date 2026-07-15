from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


SECTION_RE = re.compile(r"^# 唐開元占經 (目錄/議語|卷(\d+))\s*$", re.MULTILINE)
PAGE_RE = re.compile(r"<pb:([^>]+)>")
KR_ENTITY_RE = re.compile(r"&KR[0-9A-Fa-f]+;")


def locator_for_section(label: str, volume_number: str | None) -> str:
    if label == "目錄/議語":
        return "KR3g0018_000"
    if volume_number is None:
        raise ValueError(f"missing volume number for section {label!r}")
    return f"KR3g0018_{int(volume_number):03d}"


def split_kaiyuan_fulltext(text: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        locator = locator_for_section(match.group(1), match.group(2))
        sections[locator] = text[start:end].strip() + "\n"
    return sections


def compare_volume_text(fulltext_section: str, volume_text: str) -> dict[str, Any]:
    exact = fulltext_section == volume_text
    stripped_equal = fulltext_section.strip() == volume_text.strip()
    return {
        "exact": exact,
        "stripped_equal": stripped_equal,
        "fulltext_sha256": hashlib.sha256(fulltext_section.encode("utf-8")).hexdigest(),
        "volume_sha256": hashlib.sha256(volume_text.encode("utf-8")).hexdigest(),
    }


def audit_kaiyuan_corpus(fulltext_path: Path, volumes_dir: Path) -> dict[str, Any]:
    text = fulltext_path.read_text(encoding="utf-8")
    sections = split_kaiyuan_fulltext(text)
    expected = {f"KR3g0018_{number:03d}" for number in range(121)}
    found_files = {path.stem for path in volumes_dir.glob("KR3g0018_*.md")}

    comparisons: dict[str, Any] = {}
    for locator, section in sorted(sections.items()):
        volume_path = volumes_dir / f"{locator}.md"
        if volume_path.exists():
            comparisons[locator] = compare_volume_text(
                section,
                volume_path.read_text(encoding="utf-8"),
            )

    page_markers = PAGE_RE.findall(text)
    return {
        "schema_version": "kaiyuan-corpus-audit/v1",
        "fulltext_path": str(fulltext_path),
        "volumes_dir": str(volumes_dir),
        "section_count": len(sections),
        "expected_section_count": 121,
        "missing_sections": sorted(expected - set(sections)),
        "extra_sections": sorted(set(sections) - expected),
        "missing_volume_files": sorted(expected - found_files),
        "extra_volume_files": sorted(found_files - expected),
        "exact_equal_count": sum(1 for item in comparisons.values() if item["exact"]),
        "stripped_equal_count": sum(1 for item in comparisons.values() if item["stripped_equal"]),
        "different_volumes": sorted(
            locator for locator, item in comparisons.items() if not item["stripped_equal"]
        ),
        "page_marker_count": len(page_markers),
        "first_page_marker": page_markers[0] if page_markers else None,
        "last_page_marker": page_markers[-1] if page_markers else None,
        "kr_entity_count": len(KR_ENTITY_RE.findall(text)),
        "replacement_character_count": text.count("\ufffd"),
        "fulltext_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "comparisons": comparisons,
    }


def write_split_volumes(fulltext_path: Path, out_dir: Path) -> dict[str, Any]:
    sections = split_kaiyuan_fulltext(fulltext_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    for locator, content in sections.items():
        (out_dir / f"{locator}.md").write_text(content, encoding="utf-8")
    return {"written": len(sections), "out_dir": str(out_dir)}
