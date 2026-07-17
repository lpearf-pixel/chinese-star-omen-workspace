"""Obsidian source adapter with frontmatter, wiki links, headings and chunk metadata."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .kaiyuan_path_infer import merge_fm_with_path_defaults

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
FRONTMATTER_RE = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
HEADING_LINE_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def parse_frontmatter(raw: str) -> Tuple[Dict[str, Any], str]:
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    body = raw[match.end() :]
    if yaml is None:
        return {}, body
    try:
        metadata = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}, body
    return (metadata if isinstance(metadata, dict) else {}), body


def extract_wiki_links(text: str) -> List[str]:
    return list(dict.fromkeys(WIKI_LINK_RE.findall(text)))


def _normalize_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def sanitize_frontmatter(metadata: Dict[str, Any], max_json_bytes: int = 4096) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in metadata.items():
        if key in ("tags", "aliases", "variant_terms", "normalized_terms", "source_refs"):
            safe[key] = _normalize_str_list(value)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        elif isinstance(value, list) and all(isinstance(item, (str, int, float, bool)) for item in value[:50]):
            safe[key] = value[:50]
    raw = json.dumps(safe, ensure_ascii=False, default=str)
    if len(raw.encode("utf-8")) > max_json_bytes:
        return {"_truncated": True, "title": safe.get("title")}
    return safe


def split_by_markdown_headings(body: str) -> List[Tuple[str, str]]:
    sections: List[Tuple[str, str]] = []
    stack: List[Tuple[int, str]] = []
    buffer: List[str] = []

    def flush() -> None:
        text = "\n".join(buffer).strip()
        if text:
            heading_path = " / ".join(f"{'#' * level} {title}" for level, title in stack)
            sections.append((heading_path, text))
        buffer.clear()

    for line in body.splitlines():
        heading = HEADING_LINE_RE.match(line)
        if heading:
            flush()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
        buffer.append(line)
    flush()
    return sections or [("", body.strip())]


def work_items_for_markdown_file(
    path: Path,
    vault_root: Path,
    source_type: str,
    chunk_size: int,
    chunk_overlap: int,
    ingest_source: str,
    source_root_label: str,
) -> List[Dict[str, Any]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = parse_frontmatter(raw)
    wiki_links = extract_wiki_links(raw)
    content_hash = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    mtime = int(path.stat().st_mtime)
    absolute_path = str(path.resolve())
    doc_id = hashlib.sha1(absolute_path.encode("utf-8")).hexdigest()
    try:
        relative_path = str(path.resolve().relative_to(vault_root.resolve()))
    except ValueError:
        relative_path = path.name

    frontmatter = merge_fm_with_path_defaults(relative_path, frontmatter)
    tags = _normalize_str_list(frontmatter.get("tags"))
    aliases = _normalize_str_list(frontmatter.get("aliases"))
    safe_frontmatter = sanitize_frontmatter(frontmatter)

    from chunking import split_into_chunks

    work: List[Dict[str, Any]] = []
    chunk_index = 0
    for section_heading, section_text in split_by_markdown_headings(body):
        if not section_text.strip():
            continue
        for _, chunk_body in split_into_chunks(section_text, chunk_size, chunk_overlap):
            work.append(
                {
                    "chunk_id": f"{doc_id}:{chunk_index}",
                    "doc_id": doc_id,
                    "path": absolute_path,
                    "title": path.name,
                    "source_type": source_type,
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_body,
                    "content_hash": content_hash,
                    "mtime": mtime,
                    "ingest_source": ingest_source,
                    "source_root_label": source_root_label,
                    "relative_path": relative_path,
                    "wiki_links": wiki_links,
                    "tags": tags,
                    "aliases": aliases,
                    "section_heading": section_heading or None,
                    "frontmatter": safe_frontmatter,
                }
            )
            chunk_index += 1
    return work
