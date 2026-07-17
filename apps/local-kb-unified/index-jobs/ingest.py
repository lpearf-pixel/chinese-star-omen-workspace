#!/usr/bin/env python3
"""Scan configured knowledge sources, embed chunks with Ollama, and upsert Qdrant points.

B1 restores the real runtime. The `incremental` mode name is retained for source
compatibility, but true hash-based insert/update/delete semantics are implemented
in the following B2 phase. Destructive collection recreation requires the
explicit `--recreate` flag.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from chunking import split_into_chunks

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

TEXT_EXTENSIONS = {
    ".md", ".markdown", ".txt", ".py", ".rs", ".go", ".ts", ".tsx",
    ".js", ".jsx", ".json", ".yaml", ".yml", ".toml", ".sh",
}
SKIP_DIR_NAMES = {
    ".git", "__pycache__", ".venv", "node_modules", ".idea", ".cursor", ".obsidian",
    "incoming",
}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def resolve_sources_root() -> Path:
    raw = os.environ.get("KB_SOURCES_ROOT", "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else (REPO_ROOT / path).resolve()
    return (REPO_ROOT / "data" / "sources").resolve()


def resolve_obsidian_root() -> Optional[Path]:
    if not _env_bool("KB_ENABLE_OBSIDIAN_SOURCE"):
        return None
    raw = os.environ.get("KB_OBSIDIAN_ROOT", "").strip()
    if not raw:
        return None
    path = Path(raw)
    path = path if path.is_absolute() else (REPO_ROOT / path).resolve()
    return path if path.is_dir() else None


def detect_source_type(relative_path: Path) -> str:
    parts = relative_path.parts
    if parts and parts[0] in ("notes", "docs", "code"):
        return parts[0]
    return "docs"


def iter_source_files(root: Optional[Path]) -> Iterator[Tuple[Path, str]]:
    if root is None or not root.is_dir():
        return
    for directory, directory_names, file_names in os.walk(root, topdown=True):
        directory_names[:] = [name for name in directory_names if name not in SKIP_DIR_NAMES]
        for name in file_names:
            path = Path(directory) / name
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                relative_path = path.relative_to(root)
            except ValueError:
                continue
            yield path, detect_source_type(relative_path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def doc_id_for_path(path: str) -> str:
    return hashlib.sha1(path.encode("utf-8")).hexdigest()


def default_work_items_for_file(
    path: Path,
    source_type: str,
    chunk_size: int,
    overlap: int,
) -> List[Dict[str, Any]]:
    absolute_path = str(path.resolve())
    try:
        raw = read_text(path)
    except OSError:
        return []
    content_hash = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    mtime = int(path.stat().st_mtime)
    doc_id = doc_id_for_path(absolute_path)
    return [
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
            "ingest_source": "default",
        }
        for chunk_index, chunk_body in split_into_chunks(raw, chunk_size, overlap)
    ]


def collect_all_work_items(
    sources_root: Path,
    obsidian_root: Optional[Path],
    chunk_size: int,
    overlap: int,
) -> List[Dict[str, Any]]:
    from sources.obsidian_adapter import work_items_for_markdown_file

    source_root_label = os.environ.get("KB_OBSIDIAN_SOURCE_ROOT_LABEL", "_kb-ingest").strip() or "_kb-ingest"
    ingest_label = os.environ.get("KB_OBSIDIAN_INGEST_SOURCE_LABEL", "obsidian").strip() or "obsidian"
    work: List[Dict[str, Any]] = []
    seen_files: Set[Path] = set()

    same_root = obsidian_root is not None and obsidian_root.resolve() == sources_root.resolve()

    for path, source_type in iter_source_files(sources_root):
        resolved = path.resolve()
        if resolved in seen_files:
            continue
        seen_files.add(resolved)
        if same_root and path.suffix.lower() in (".md", ".markdown"):
            work.extend(
                work_items_for_markdown_file(
                    path,
                    sources_root,
                    source_type,
                    chunk_size,
                    overlap,
                    ingest_source=ingest_label,
                    source_root_label=source_root_label,
                )
            )
        else:
            work.extend(default_work_items_for_file(path, source_type, chunk_size, overlap))

    if obsidian_root is not None and not same_root:
        for path, source_type in iter_source_files(obsidian_root):
            resolved = path.resolve()
            if resolved in seen_files:
                continue
            seen_files.add(resolved)
            if path.suffix.lower() in (".md", ".markdown"):
                work.extend(
                    work_items_for_markdown_file(
                        path,
                        obsidian_root,
                        source_type,
                        chunk_size,
                        overlap,
                        ingest_source=ingest_label,
                        source_root_label=source_root_label,
                    )
                )
            else:
                work.extend(default_work_items_for_file(path, source_type, chunk_size, overlap))
    return work


_FRONTMATTER_TOPLEVEL_KEYS = (
    "kb_book_id", "book_title", "card_type", "evidence_level", "final_citable",
    "query_mode_hint", "variant_terms", "normalized_terms", "source_locator",
    "source_refs", "volume", "section", "anchor_text", "paragraph_index",
)


def _promote_frontmatter_to_payload(frontmatter: Dict[str, Any], payload: Dict[str, Any]) -> None:
    for key in _FRONTMATTER_TOPLEVEL_KEYS:
        if key not in frontmatter or frontmatter[key] is None:
            continue
        value = frontmatter[key]
        if key in ("variant_terms", "normalized_terms", "source_refs"):
            if isinstance(value, list):
                payload[key] = [str(item) for item in value if item is not None][:50]
            else:
                payload[key] = [str(value)]
        else:
            payload[key] = value


def ollama_embed(host: str, port: int, model: str, text: str) -> List[float]:
    response = requests.post(
        f"http://{host}:{port}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    vector = data.get("embedding")
    if not vector:
        raise RuntimeError(f"No embedding in response: {data}")
    return vector


def build_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "doc_id": item["doc_id"],
        "chunk_id": item["chunk_id"],
        "source_type": item["source_type"],
        "path": item["path"],
        "title": item["title"],
        "chunk_text": item["chunk_text"],
        "chunk_index": item["chunk_index"],
        "mtime": item["mtime"],
        "content_hash": item["content_hash"],
        "ingest_source": item.get("ingest_source", "default"),
    }
    if item["source_type"] == "code" and item["path"].endswith(".py"):
        payload["lang"] = "python"

    obsidian_label = os.environ.get("KB_OBSIDIAN_INGEST_SOURCE_LABEL", "obsidian").strip() or "obsidian"
    if item.get("ingest_source") == obsidian_label:
        for key in (
            "relative_path", "source_root_label", "wiki_links", "tags", "aliases",
            "section_heading", "frontmatter",
        ):
            if item.get(key):
                payload[key] = item[key]

    frontmatter = item.get("frontmatter")
    if isinstance(frontmatter, dict):
        _promote_frontmatter_to_payload(frontmatter, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Index knowledge sources into Qdrant")
    parser.add_argument("--mode", choices=("full", "incremental"), default="full")
    parser.add_argument("--recreate", action="store_true", help="Explicitly delete and recreate the target collection")
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--chunk-overlap", type=int, default=120)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--collection",
        default=os.environ.get("KB_SEARCH_DEFAULT_COLLECTION", "local_kb_kaiyuan_v2"),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ollama_host = os.environ.get("OLLAMA_HOST", "127.0.0.1")
    ollama_port = _env_int("OLLAMA_PORT", 11434)
    qdrant_host = os.environ.get("QDRANT_HOST", "127.0.0.1")
    qdrant_port = _env_int("QDRANT_HTTP_PORT", 6333)
    embed_model = os.environ.get("EMBED_MODEL", "nomic-embed-text")

    sources_root = resolve_sources_root()
    obsidian_root = resolve_obsidian_root()
    client = QdrantClient(url=f"http://{qdrant_host}:{qdrant_port}", timeout=120)

    print(f"sources_root={sources_root}")
    print(f"obsidian_root={obsidian_root if obsidian_root else '(disabled)'}")
    print(f"collection={args.collection}")
    print(f"mode={args.mode}")

    if args.dry_run:
        primary_files = list(iter_source_files(sources_root))
        obsidian_files = list(iter_source_files(obsidian_root)) if obsidian_root else []
        print(f"files_primary={len(primary_files)}")
        if obsidian_root and obsidian_root.resolve() != sources_root.resolve():
            print(f"files_obsidian_tree={len(obsidian_files)}")
        for path, source_type in primary_files[:15]:
            print(f"  [primary {source_type}] {path}")
        return 0

    work = collect_all_work_items(sources_root, obsidian_root, args.chunk_size, args.chunk_overlap)
    print(f"chunks_total={len(work)}")
    if not work:
        print("No chunks to index", file=sys.stderr)
        return 0

    dimension = len(ollama_embed(ollama_host, ollama_port, embed_model, work[0]["chunk_text"][:2000]))
    print(f"embedding_dim={dimension}")

    if args.recreate:
        try:
            client.delete_collection(args.collection)
            print(f"deleted collection {args.collection}")
        except Exception:
            pass
        client.create_collection(
            collection_name=args.collection,
            vectors_config=qm.VectorParams(size=dimension, distance=qm.Distance.COSINE),
        )
        print(f"created collection {args.collection}")
    else:
        try:
            client.get_collection(args.collection)
        except Exception:
            client.create_collection(
                collection_name=args.collection,
                vectors_config=qm.VectorParams(size=dimension, distance=qm.Distance.COSINE),
            )
            print(f"created collection {args.collection}")

    batch: List[qm.PointStruct] = []
    upserted = 0
    errors = 0
    started = time.perf_counter()

    def flush_batch() -> None:
        nonlocal batch, upserted
        if not batch:
            return
        client.upsert(collection_name=args.collection, points=batch)
        upserted += len(batch)
        batch = []

    for item in work:
        try:
            vector = ollama_embed(
                ollama_host,
                ollama_port,
                embed_model,
                item["chunk_text"][:8000],
            )
        except Exception as exc:
            print(f"embed error chunk {item['chunk_id']}: {exc}", file=sys.stderr)
            errors += 1
            continue

        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, item["chunk_id"]))
        batch.append(qm.PointStruct(id=point_id, vector=vector, payload=build_payload(item)))
        if len(batch) >= args.batch_size:
            flush_batch()

    flush_batch()
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    print(f"ingest_finished points_upserted={upserted} errors={errors} elapsed_ms={elapsed_ms}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
