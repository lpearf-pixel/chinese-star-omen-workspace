from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic_ns
from typing import Any, Callable

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "kb-contracts" / "python"
if str(CONTRACTS) not in sys.path:
    sys.path.insert(0, str(CONTRACTS))

from kb_contracts import (  # noqa: E402
    SyncErrorCode,
    SyncRunStatus,
    load_candidate_manifest,
    sha256_text,
)
from src.connectors.kb_search_retriever import KBSearchError, KBSearchRetriever  # noqa: E402
from src.observability import base_observability, elapsed_ms  # noqa: E402

SYNC_STATUSES = ("merged", "needs_review", "pending", "stale")


def _empty_counts() -> dict[str, int]:
    return {status: 0 for status in SYNC_STATUSES}


def _normalize_anchor(value: Any) -> str:
    return "".join(str(value or "").split())


def _parse_card_metadata(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise ValueError("PyYAML is required to inspect candidate cards")
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("candidate card has no YAML frontmatter")
    try:
        _, raw, _body = text.split("---", 2)
    except ValueError as exc:
        raise ValueError("candidate card has unterminated frontmatter") from exc
    parsed = yaml.safe_load(raw) or {}
    if not isinstance(parsed, dict):
        raise ValueError("candidate card frontmatter must be a mapping")
    return parsed


def _resolve_source_file(source_value: str, sources_root: Path) -> Path | None:
    if not source_value:
        return None
    raw = Path(source_value).expanduser()
    candidates = [raw] if raw.is_absolute() else [sources_root / raw, raw]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _local_candidate_is_stale(
    *,
    item: dict[str, Any],
    card_path: Path,
    sources_root: Path,
) -> tuple[bool, str | None]:
    if not card_path.is_file():
        return True, "missing_candidate_card"
    try:
        metadata = _parse_card_metadata(card_path)
    except (OSError, UnicodeError, ValueError) as exc:
        return True, f"invalid_candidate_card:{exc}"

    item_anchor = str(item.get("anchor_text") or "")
    item_hash = str(item.get("content_hash") or "")
    card_anchor = str(metadata.get("anchor_text") or "")
    card_hash = str(metadata.get("content_hash") or "")
    if not item_anchor or not item_hash:
        return True, "missing_manifest_anchor_or_hash"
    if not card_anchor or not card_hash:
        return True, "missing_candidate_anchor_or_hash"
    if _normalize_anchor(card_anchor) != _normalize_anchor(item_anchor):
        return True, "candidate_anchor_mismatch"
    if card_hash != item_hash:
        return True, "candidate_hash_mismatch"
    if sha256_text(item_anchor) != item_hash:
        return True, "manifest_hash_mismatch"

    item_locator = str(item.get("source_locator") or "")
    card_locator = str(metadata.get("source_locator") or "")
    if item_locator and card_locator != item_locator:
        return True, "candidate_source_locator_mismatch"

    source_value = str(metadata.get("source_file") or "")
    source_path = _resolve_source_file(source_value, sources_root)
    if source_path is None:
        return True, "missing_source"
    try:
        source_text = source_path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        return True, f"source_read_error:{exc}"
    if _normalize_anchor(item_anchor) not in _normalize_anchor(source_text):
        return True, "source_anchor_mismatch"
    return False, None


def _hit_metadata(hit: dict[str, Any]) -> dict[str, Any]:
    metadata = hit.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _hit_card_type(hit: dict[str, Any]) -> str:
    metadata = _hit_metadata(hit)
    return str(hit.get("card_type") or metadata.get("card_type") or "")


def _hit_content_hash(hit: dict[str, Any]) -> str:
    metadata = _hit_metadata(hit)
    return str(hit.get("content_hash") or metadata.get("content_hash") or "")


def _hit_source_locator(hit: dict[str, Any]) -> str:
    metadata = _hit_metadata(hit)
    return str(hit.get("source_locator") or metadata.get("source_locator") or "")


def _classify_hits(item: dict[str, Any], hits: list[dict[str, Any]]) -> str:
    """Classify official extract-card hits using content and source identity."""

    relevant = [
        hit
        for hit in hits
        if _hit_card_type(hit) in {"", "extract_card"}
    ]
    expected_hash = str(item.get("content_hash") or "")
    expected_locator = str(item.get("source_locator") or "")
    if expected_hash and expected_locator and any(
        _hit_content_hash(hit) == expected_hash
        and _hit_source_locator(hit) == expected_locator
        for hit in relevant
    ):
        return "merged"
    if relevant:
        return "needs_review"
    return "pending"


def _official_extract_hits(
    retriever: KBSearchRetriever,
    *,
    book_id: str,
    item: dict[str, Any],
) -> list[dict[str, Any]]:
    result = retriever.retrieve(
        str(item.get("term") or item.get("anchor_text") or ""),
        top_k=20,
        filters={"kb_book_id": book_id},
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
            details={
                "response_keys": sorted(result) if isinstance(result, dict) else []
            },
        )
    return [hit for hit in hits if isinstance(hit, dict)]


def _atomic_write_manifests(planned: list[tuple[Path, dict[str, Any]]]) -> None:
    staged: list[tuple[Path, Path]] = []
    originals: dict[Path, bytes | None] = {}
    replaced: list[Path] = []
    try:
        for path, manifest in planned:
            path.parent.mkdir(parents=True, exist_ok=True)
            originals[path] = path.read_bytes() if path.exists() else None
            temporary = path.with_suffix(path.suffix + ".sync.tmp")
            temporary.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False)
                + "\n",
                encoding="utf-8",
            )
            staged.append((temporary, path))
        for temporary, path in staged:
            temporary.replace(path)
            replaced.append(path)
    except Exception:
        for path in replaced:
            original = originals.get(path)
            if original is None:
                path.unlink(missing_ok=True)
            else:
                restore = path.with_suffix(path.suffix + ".restore.tmp")
                restore.write_bytes(original)
                restore.replace(path)
        raise
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def _error_report(
    *,
    book_id: str,
    manifests: list[Path],
    total_items: int,
    checked: int,
    exc: KBSearchError,
    upstream_meta: dict[str, Any] | None = None,
    started_ns: int,
    lookup_count: int,
    official_hit_count: int,
) -> dict[str, Any]:
    error = exc.to_dict()
    report = {
        "schema_version": "candidate-sync-report/v2",
        "run_status": SyncRunStatus.ERROR.value,
        "book_id": book_id,
        "upstream_meta": upstream_meta,
        "manifests": [str(path) for path in manifests],
        "checked": checked,
        "preserved": total_items,
        "updated": _empty_counts(),
        "error": error,
    }
    report["observability"] = base_observability(
        "candidate_sync",
        latency_ms=elapsed_ms(started_ns, monotonic_ns()),
        collection=(upstream_meta or {}).get("collection"),
        corpus_version=(upstream_meta or {}).get("corpus_version"),
        checked=checked,
        lookup_count=lookup_count,
        official_hit_count=official_hit_count,
        run_error=error,
    )
    return report


def sync_candidate_manifests(
    book_id: str,
    candidate_root: Path,
    *,
    retriever: KBSearchRetriever,
    now: str | None = None,
    retrieve_hits: Callable[[dict[str, Any]], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Plan all item statuses, then atomically write manifests on full success."""

    started_ns = monotonic_ns()
    lookup_count = 0
    official_hit_count = 0
    manifest_paths = sorted(
        candidate_root.glob(f"extract_cards/{book_id}/candidate_manifest.json")
    )
    loaded = [(path, load_candidate_manifest(path)) for path in manifest_paths]
    total_items = sum(len(manifest.get("items") or []) for _, manifest in loaded)

    try:
        upstream_meta = retriever.get_upstream_meta()
        if (
            not isinstance(upstream_meta, dict)
            or upstream_meta.get("meta_status", "ok") != "ok"
        ):
            raise KBSearchError(
                "upstream corpus metadata is not ready",
                code=SyncErrorCode.INVALID_RESPONSE,
                details={"upstream_meta": upstream_meta},
            )
    except KBSearchError as exc:
        return _error_report(
            book_id=book_id,
            manifests=manifest_paths,
            total_items=total_items,
            checked=0,
            exc=exc,
            started_ns=started_ns,
            lookup_count=lookup_count,
            official_hit_count=official_hit_count,
        )

    timestamp = now or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    sources_root = Path(str(retriever.settings.kb_sources_root)).expanduser()
    counts = _empty_counts()
    checked = 0
    planned: list[tuple[Path, dict[str, Any]]] = []

    try:
        for manifest_path, original in loaded:
            manifest = copy.deepcopy(original)
            manifest["current_upstream_corpus_version"] = upstream_meta.get(
                "corpus_version"
            )
            manifest["last_synced_at"] = timestamp
            for item in manifest.get("items", []):
                card_path = manifest_path.parent / str(item.get("file") or "")
                stale, reason = _local_candidate_is_stale(
                    item=item,
                    card_path=card_path,
                    sources_root=sources_root,
                )
                if stale:
                    status = "stale"
                    item["sync_validation"] = {
                        "local_status": "stale",
                        "reason": reason,
                    }
                else:
                    lookup_count += 1
                    hits = (
                        retrieve_hits(item)
                        if retrieve_hits is not None
                        else _official_extract_hits(
                            retriever,
                            book_id=book_id,
                            item=item,
                        )
                    )
                    if not isinstance(hits, list):
                        raise KBSearchError(
                            "candidate sync hit provider must return a list",
                            code=SyncErrorCode.INVALID_RESPONSE,
                        )
                    official_hit_count += len(hits)
                    status = _classify_hits(item, hits)
                    item["sync_validation"] = {
                        "local_status": "current",
                        "official_hit_count": len(hits),
                        "source_locator": item.get("source_locator"),
                    }
                item["sync_status"] = status
                counts[status] += 1
                checked += 1
            manifest["last_sync_report"] = {
                "schema_version": "candidate-sync-report/v2",
                "run_status": SyncRunStatus.OK.value,
                "synced_at": timestamp,
                "updated": dict(counts),
            }
            planned.append((manifest_path, manifest))
    except KBSearchError as exc:
        return _error_report(
            book_id=book_id,
            manifests=manifest_paths,
            total_items=total_items,
            checked=checked,
            exc=exc,
            upstream_meta=upstream_meta,
            started_ns=started_ns,
            lookup_count=lookup_count,
            official_hit_count=official_hit_count,
        )

    _atomic_write_manifests(planned)
    report = {
        "schema_version": "candidate-sync-report/v2",
        "run_status": SyncRunStatus.OK.value,
        "book_id": book_id,
        "upstream_meta": upstream_meta,
        "manifests": [str(path) for path in manifest_paths],
        "checked": checked,
        "preserved": 0,
        "updated": counts,
        "error": None,
    }
    report["observability"] = base_observability(
        "candidate_sync",
        latency_ms=elapsed_ms(started_ns, monotonic_ns()),
        collection=upstream_meta.get("collection"),
        corpus_version=upstream_meta.get("corpus_version"),
        checked=checked,
        lookup_count=lookup_count,
        official_hit_count=official_hit_count,
        run_error=None,
    )
    return report
