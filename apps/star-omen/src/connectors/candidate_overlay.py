from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

CONTRACTS = Path(__file__).resolve().parents[4] / "packages" / "kb-contracts" / "python"
if str(CONTRACTS) not in sys.path:
    sys.path.insert(0, str(CONTRACTS))
from kb_contracts import load_candidate_manifest  # noqa: E402


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or yaml is None:
        return {}, text
    _, fm, body = text.split("---", 2)
    return yaml.safe_load(fm) or {}, body.lstrip("\n")


def overlay_hits(root: Path, query: str, *, book_id: str | None = None, limit: int = 3) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    variants = {query, query.replace(" ", ""), query.translate(str.maketrans({"荧": "熒"})), query.translate(str.maketrans({"熒": "荧"}))}
    hits: list[dict[str, Any]] = []
    manifests = sorted(root.glob("extract_cards/*/candidate_manifest.json"))
    for manifest_path in manifests:
        try:
            manifest = load_candidate_manifest(manifest_path)
        except Exception:
            continue
        if book_id and manifest.get("book_id") != book_id:
            continue
        for item in manifest.get("items", []):
            if item.get("review_status") != "pending" or item.get("sync_status") not in {"pending", "needs_review"}:
                continue
            card_path = manifest_path.parent / str(item.get("file"))
            if not card_path.exists():
                continue
            meta, body = parse_frontmatter(card_path)
            haystack = f"{meta.get('term','')} {meta.get('anchor_text','')} {body}".replace(" ", "")
            if not any(v.replace(" ", "") in haystack for v in variants if v):
                continue
            kb_book_id = meta.get("kb_book_id") or manifest.get("book_id")
            hits.append({
                "chunk_id": f"candidate-overlay:{item.get('id')}",
                "score": 0.5,
                "path": str(card_path),
                "snippet": str(meta.get("anchor_text") or body[:200]),
                "title": str(meta.get("term") or item.get("term")),
                "book_title": meta.get("book_title"),
                "kb_book_id": kb_book_id,
                "book_id": kb_book_id,
                "card_type": "extract_card",
                "evidence_level": "candidate",
                "source_namespace": "downstream_generated",
                "review_status": item.get("review_status"),
                "sync_status": item.get("sync_status"),
                "content_hash": item.get("content_hash"),
                "source_locator": item.get("source_locator"),
                "anchor_text": item.get("anchor_text"),
            })
            if len(hits) >= limit:
                return hits
    return hits
