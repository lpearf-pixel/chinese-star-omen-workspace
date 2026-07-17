from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "kb-contracts" / "python"
if str(CONTRACTS) not in sys.path:
    sys.path.insert(0, str(CONTRACTS))
from kb_contracts import (  # noqa: E402
    SyncErrorCode,
    load_candidate_manifest,
    merge_candidate_item,
    new_candidate_manifest,
    save_candidate_manifest,
    sha256_text,
    stable_candidate_id,
)

from src.candidate_sync import sync_candidate_manifests
from src.connectors.kb_search_retriever import KBSearchError, KBSearchRetriever

BOOK_TITLES = {"kaiyuan_zhanjing": "唐開元占經"}


def _aliases(term: str) -> list[str]:
    compact = term.replace(" ", "")
    trad = compact.translate(str.maketrans({"荧": "熒"}))
    simp = compact.translate(str.maketrans({"熒": "荧"}))
    vals = [trad, simp, f"{simp[:2]} {simp[2:]}", f"{trad[:2]} {trad[2:]}"]
    out: list[str] = []
    for value in vals:
        if value and value not in out:
            out.append(value)
    return out


def _safe_file_part(value: str) -> str:
    safe = re.sub(r"[^0-9A-Za-z_.-]+", "_", str(value)).strip("._")
    return safe or "source"


def _source_locator(path: str) -> str:
    normalized = path.replace("\\", "/")
    if "全文合併版" in normalized or "全文合并版" in normalized:
        return "fulltext"
    match = re.search(r"(KR\w+_\d+)", normalized)
    return match.group(1) if match else _safe_file_part(Path(normalized).stem)


def _volume(locator: str) -> str:
    match = re.search(r"_(\d+)$", locator)
    return f"卷{int(match.group(1))}" if match else "unknown"


def _rel_source(path: str) -> str:
    marker = "/古籍/"
    normalized = path.replace("\\", "/")
    if marker in normalized:
        return normalized.split(marker, 1)[1].join(["古籍/", ""])
    return normalized


def _write_card(path: Path, meta: dict[str, Any], body: str) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is required to write candidate cards")
    path.write_text(
        "---\n"
        + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + body,
        encoding="utf-8",
    )


def _candidate_upstream_meta(retriever: KBSearchRetriever) -> dict[str, Any]:
    """Read upstream metadata without making local extraction depend on it."""

    try:
        metadata = retriever.get_upstream_meta()
    except KBSearchError as exc:
        return {
            "meta_status": "unavailable",
            "error_code": "UPSTREAM_META_UNAVAILABLE",
            "message": str(exc),
        }
    return dict(metadata)


def _base_meta_values(upstream_meta: dict[str, Any]) -> tuple[str, str, str]:
    status = str(upstream_meta.get("meta_status") or "ok")
    corpus_version = str(upstream_meta.get("corpus_version") or status)
    ingest_run_id = str(upstream_meta.get("ingest_run_id") or status)
    return status, corpus_version, ingest_run_id


def generate_candidate_cards(
    query: str,
    book_id: str,
    out_dir: Path,
    *,
    base_url: str | None = None,
) -> dict[str, Any]:
    retriever = KBSearchRetriever(base_url=base_url)
    upstream_meta = _candidate_upstream_meta(retriever)
    base_meta_status, base_corpus_version, base_ingest_run_id = _base_meta_values(
        upstream_meta
    )
    variants = retriever._query_variants(query)
    hits, scan_stats = retriever._scan_primary_files(
        query,
        book_id=book_id,
        mode="evidence",
        limit=100,
        query_variants=variants,
    )
    hits = [
        hit
        for hit in hits
        if hit.get("card_type") in {"fenjuan", "fulltext"}
        and hit.get("match_type") in {"exact_raw", "exact_normalized"}
    ]
    if hits:
        max_heading_hits = max(
            int(hit.get("heading_term_hits") or 0) for hit in hits
        )
        if max_heading_hits > 0:
            hits = [
                hit
                for hit in hits
                if int(hit.get("heading_term_hits") or 0) == max_heading_hits
            ]
        else:
            source_counts: dict[str, int] = {}
            for hit in hits:
                locator = str(hit.get("source_locator") or "")
                source_counts[locator] = source_counts.get(locator, 0) + int(
                    hit.get("match_count") or 1
                )
            best_count = max(source_counts.values())
            best_sources = {
                locator
                for locator, count in source_counts.items()
                if count == best_count
            }
            hits = [
                hit
                for hit in hits
                if str(hit.get("source_locator") or "") in best_sources
            ]
        hits.sort(
            key=lambda hit: (
                str(hit.get("source_locator") or ""),
                int(hit.get("match_offset") or 0),
            )
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "candidate_manifest.json"
    manifest = (
        load_candidate_manifest(manifest_path)
        if manifest_path.exists()
        else new_candidate_manifest(
            book_id,
            base_corpus_version=base_corpus_version,
            base_ingest_run_id=base_ingest_run_id,
        )
    )

    generated: list[str] = []
    for hit in hits:
        source_path = Path(str(hit.get("path") or ""))
        if not source_path.exists():
            continue
        match_offset = hit.get("match_offset")
        if not isinstance(match_offset, int):
            continue

        source_locator = str(
            hit.get("source_locator") or _source_locator(str(source_path))
        )
        source_volume = str(hit.get("source_volume") or _volume(source_locator))
        page_marker = hit.get("page_marker")
        anchor_text = str(
            hit.get("anchor_text")
            or hit.get("excerpt")
            or hit.get("snippet")
            or ""
        ).strip()
        if not anchor_text:
            continue

        content_hash = sha256_text(anchor_text)
        candidate_id = stable_candidate_id(
            book_id,
            query,
            source_locator,
            match_offset,
        )
        page_part = _safe_file_part(str(page_marker or "no-page"))
        file_name = (
            f"{candidate_id.split(':')[1]}."
            f"{_safe_file_part(source_locator)}.{page_part}.{match_offset}.md"
        )
        card_path = out_dir / file_name
        aliases = _aliases(query)
        heading_path = (
            hit.get("heading_path")
            if isinstance(hit.get("heading_path"), list)
            else []
        )
        paragraph_index = hit.get("paragraph_index")
        if not isinstance(paragraph_index, int):
            paragraph_index = 0

        card_meta = {
            "schema_version": "candidate-card/v1",
            "kb_book_id": book_id,
            "book_title": BOOK_TITLES.get(book_id, book_id),
            "card_type": "extract_card",
            "evidence_level": "candidate",
            "source_namespace": "downstream_generated",
            "generated_by": "codex_ready_filesystem_fallback",
            "generated_status": "candidate",
            "review_status": "pending",
            "sync_status": "pending",
            "term": query,
            "aliases": aliases,
            "source_file": _rel_source(str(source_path)),
            "source_locator": source_locator,
            "source_volume": source_volume,
            "page_marker": page_marker,
            "heading_path": heading_path,
            "paragraph_index": paragraph_index,
            "match_type": "exact_phrase",
            "source_match_type": hit.get("match_type"),
            "match_offset": match_offset,
            "match_end": hit.get("match_end"),
            "match_count": int(hit.get("match_count") or 1),
            "matched_variants": hit.get("matched_variants") or [],
            "anchor_text": anchor_text,
            "content_hash": content_hash,
            "base_meta_status": base_meta_status,
            "base_corpus_version": base_corpus_version,
            "base_ingest_run_id": base_ingest_run_id,
        }
        body = (
            f"# {query} / {aliases[0] if aliases else query}\n\n"
            f"## 原文证据\n\n{anchor_text}\n\n"
            "## 来源\n\n"
            f"- 书名：{card_meta['book_title']}\n"
            f"- 卷次：{source_volume}\n"
            f"- 文件：{card_meta['source_file']}\n"
            f"- offset：{match_offset}\n"
            f"- page_marker：{page_marker}\n"
        )
        _write_card(card_path, card_meta, body)
        item = {
            "id": candidate_id,
            "file": file_name,
            "term": query,
            "source_locator": source_locator,
            "source_volume": source_volume,
            "match_offset": match_offset,
            "content_hash": content_hash,
            "anchor_text": anchor_text,
            "review_status": "pending",
            "sync_status": "pending",
        }
        merge_candidate_item(manifest, item)
        generated.append(str(card_path))

    save_candidate_manifest(manifest_path, manifest)
    return {
        "generated": generated,
        "manifest": str(manifest_path),
        "scan_stats": scan_stats,
        "upstream_meta": upstream_meta,
        "message": (
            "candidate cards generated; submit to upstream "
            "Local-KB-Unified after review."
        ),
    }


def _retrieve_hits(base_url: str, term: str) -> list[dict[str, Any]]:
    """Authenticated official extract-card lookup retained as a test seam."""

    retriever = KBSearchRetriever(base_url=base_url)
    result = retriever.retrieve(
        term,
        top_k=20,
        query_mode="evidence",
        retrieval_stage="structured_recall",
        card_types=["extract_card"],
        literal_first=True,
    )
    hits = result.get("hits")
    if not isinstance(hits, list):
        raise KBSearchError(
            "retrieve response field 'hits' must be a list",
            code=SyncErrorCode.INVALID_RESPONSE,
        )
    return [hit for hit in hits if isinstance(hit, dict)]


def sync_upstream_status(
    book_id: str,
    candidate_root: Path,
    base_url: str,
) -> dict[str, Any]:
    retriever = KBSearchRetriever(base_url=base_url)
    return sync_candidate_manifests(
        book_id,
        candidate_root,
        retriever=retriever,
        retrieve_hits=lambda item: _retrieve_hits(
            base_url,
            str(item.get("term") or item.get("anchor_text") or ""),
        ),
    )
