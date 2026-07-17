from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from typing import Any, Iterator

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
TEXT_CORE = WORKSPACE_ROOT / "packages" / "kb-text-core" / "python"
if str(TEXT_CORE) not in sys.path:
    sys.path.insert(0, str(TEXT_CORE))

from kb_text_core import (  # noqa: E402
    KaiyuanPassage,
    dedupe_kaiyuan_passages,
    parse_kaiyuan_passages,
)

from incremental import COLLECTION_SCHEMA, MANAGED_BY, point_id_for_item  # noqa: E402
from sources.kaiyuan_path_infer import path_defaults  # noqa: E402
from sources.obsidian_adapter import (  # noqa: E402
    parse_frontmatter,
    sanitize_frontmatter,
    work_items_for_markdown_file,
)

TEXT_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".py",
    ".rs",
    ".go",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sh",
}
SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".idea",
    ".cursor",
    ".obsidian",
    "incoming",
}
PRIMARY_CARD_TYPES = {"fenjuan", "fulltext"}


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stable_doc_id(source_root_label: str, relative_path: str) -> str:
    value = f"{source_root_label}:{relative_path}"
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def iter_source_files(root: Path | None) -> Iterator[tuple[Path, str]]:
    if root is None or not root.is_dir():
        return
    for directory, directory_names, file_names in os.walk(root, topdown=True):
        directory_names[:] = [
            name for name in directory_names if name not in SKIP_DIR_NAMES
        ]
        for name in sorted(file_names):
            path = Path(directory) / name
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                relative = path.relative_to(root)
            except ValueError:
                continue
            parts = relative.parts
            source_type = (
                parts[0]
                if parts and parts[0] in {"notes", "docs", "code"}
                else "docs"
            )
            yield path, source_type


def _relative_path(path: Path, root: Path) -> str:
    try:
        value = path.resolve().relative_to(root.resolve())
    except ValueError:
        value = Path(path.name)
    return str(value).replace("\\", "/")


def _approved_generated(metadata: dict[str, Any]) -> bool:
    return (
        str(metadata.get("review_status") or "") == "approved"
        or str(metadata.get("source_namespace") or "") == "official"
    )


def _merge_metadata(relative_path: str, frontmatter: dict[str, Any]) -> dict[str, Any]:
    return {**path_defaults(relative_path), **frontmatter}


def _generic_file_items(
    path: Path,
    root: Path,
    *,
    source_type: str,
    chunk_size: int,
    overlap: int,
    ingest_source: str,
    source_root_label: str,
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    relative_path = _relative_path(path, root)
    if path.suffix.lower() in {".md", ".markdown"}:
        items = work_items_for_markdown_file(
            path,
            root,
            source_type,
            chunk_size,
            overlap,
            ingest_source=ingest_source,
            source_root_label=source_root_label,
        )
    else:
        from chunking import split_into_chunks

        raw = path.read_text(encoding="utf-8", errors="replace")
        items = [
            {
                "path": str(path.resolve()),
                "title": path.name,
                "source_type": source_type,
                "chunk_index": index,
                "chunk_text": chunk,
                "mtime": int(path.stat().st_mtime),
                "ingest_source": ingest_source,
                "source_root_label": source_root_label,
                "relative_path": relative_path,
                "frontmatter": {},
            }
            for index, chunk in split_into_chunks(raw, chunk_size, overlap)
        ]

    output: list[dict[str, Any]] = []
    safe_metadata = sanitize_frontmatter(metadata)
    for item in items:
        chunk_text = str(item.get("chunk_text") or "").strip()
        if not chunk_text:
            continue
        item = dict(item)
        item["relative_path"] = relative_path
        item["source_root_label"] = source_root_label
        item["doc_id"] = _stable_doc_id(source_root_label, relative_path)
        item["source_content_hash"] = item.get("content_hash")
        item["content_hash"] = _sha256_text(chunk_text)
        item["frontmatter"] = safe_metadata
        item["managed_by"] = MANAGED_BY
        item["collection_schema"] = COLLECTION_SCHEMA
        for key, value in metadata.items():
            if value is not None:
                item[key] = value
        item["chunk_id"] = point_id_for_item(item)
        output.append(item)
    return output


def _passage_item(
    passage: KaiyuanPassage,
    source_metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    item = passage.to_dict()
    metadata = source_metadata[passage.source_path]
    item.update(
        {
            "doc_id": hashlib.sha1(
                f"{passage.kb_book_id}:{passage.source_locator}".encode("utf-8")
            ).hexdigest(),
            "path": passage.source_path,
            "title": Path(passage.source_path).name,
            "source_type": metadata["source_type"],
            "chunk_index": passage.paragraph_index,
            "chunk_text": passage.raw_text,
            "content_hash": passage.raw_content_hash,
            "mtime": metadata["mtime"],
            "ingest_source": metadata["ingest_source"],
            "source_root_label": metadata["source_root_label"],
            "relative_path": metadata["relative_path"],
            "evidence_level": "primary",
            "final_citable": True,
            "query_mode_hint": "evidence",
            "managed_by": MANAGED_BY,
            "collection_schema": COLLECTION_SCHEMA,
            "source_refs": list(passage.duplicate_sources),
        }
    )
    item["chunk_id"] = point_id_for_item(item)
    return item


def collect_desired_items(
    sources_root: Path,
    *,
    generated_root: Path,
    obsidian_root: Path | None,
    chunk_size: int,
    overlap: int,
) -> list[dict[str, Any]]:
    """Collect the complete desired managed corpus before reconciliation."""

    obsidian_label = (
        os.environ.get("KB_OBSIDIAN_INGEST_SOURCE_LABEL", "obsidian").strip()
        or "obsidian"
    )
    obsidian_root_label = (
        os.environ.get("KB_OBSIDIAN_SOURCE_ROOT_LABEL", "_kb-ingest").strip()
        or "_kb-ingest"
    )
    roots: list[tuple[Path, str, str, bool]] = [
        (sources_root, "default", "primary", False),
        (generated_root, "generated", "generated", True),
    ]
    if obsidian_root is not None:
        roots.append(
            (obsidian_root, obsidian_label, obsidian_root_label, False)
        )

    generic_items: list[dict[str, Any]] = []
    primary_passages: list[KaiyuanPassage] = []
    passage_source_metadata: dict[str, dict[str, Any]] = {}
    seen_files: set[Path] = set()

    for root, ingest_source, source_root_label, approved_only in roots:
        if not root.is_dir():
            continue
        for path, source_type in iter_source_files(root):
            resolved = path.resolve()
            if resolved in seen_files:
                continue
            seen_files.add(resolved)

            relative_path = _relative_path(path, root)
            raw = path.read_text(encoding="utf-8", errors="replace")
            frontmatter, _ = parse_frontmatter(raw)
            metadata = _merge_metadata(relative_path, frontmatter)
            if approved_only and not _approved_generated(metadata):
                continue

            card_type = str(metadata.get("card_type") or "")
            kb_book_id = str(metadata.get("kb_book_id") or "")
            if (
                path.suffix.lower() in {".md", ".markdown"}
                and kb_book_id == "kaiyuan_zhanjing"
                and card_type in PRIMARY_CARD_TYPES
            ):
                source_path = str(resolved)
                passages = parse_kaiyuan_passages(
                    raw,
                    source_path=source_path,
                    card_type=card_type,
                    kb_book_id=kb_book_id,
                    book_title=str(metadata.get("book_title") or "唐開元占經"),
                )
                primary_passages.extend(passages)
                passage_source_metadata[source_path] = {
                    "source_type": source_type,
                    "mtime": int(path.stat().st_mtime),
                    "ingest_source": ingest_source,
                    "source_root_label": source_root_label,
                    "relative_path": relative_path,
                }
                continue

            generic_items.extend(
                _generic_file_items(
                    path,
                    root,
                    source_type=source_type,
                    chunk_size=chunk_size,
                    overlap=overlap,
                    ingest_source=ingest_source,
                    source_root_label=source_root_label,
                    metadata=metadata,
                )
            )

    primary_items = [
        _passage_item(passage, passage_source_metadata)
        for passage in dedupe_kaiyuan_passages(primary_passages)
    ]
    desired = [*primary_items, *generic_items]
    desired.sort(key=point_id_for_item)
    return desired
