from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "kb-contracts" / "python"
if str(CONTRACTS) not in sys.path:
    sys.path.insert(0, str(CONTRACTS))
from kb_contracts import load_candidate_manifest, merge_candidate_item, new_candidate_manifest, save_candidate_manifest, sha256_text, stable_candidate_id  # noqa: E402

from src.connectors.kb_search_retriever import KBSearchRetriever

BOOK_TITLES = {"kaiyuan_zhanjing": "唐開元占經"}


def _aliases(term: str) -> list[str]:
    compact = term.replace(" ", "")
    trad = compact.translate(str.maketrans({"荧": "熒"}))
    simp = compact.translate(str.maketrans({"熒": "荧"}))
    vals = [trad, simp, f"{simp[:2]} {simp[2:]}", f"{trad[:2]} {trad[2:]}"]
    out: list[str] = []
    for v in vals:
        if v and v not in out:
            out.append(v)
    return out


def _source_locator(path: str) -> str:
    m = re.search(r"(KR\w+_\d+)", path)
    return m.group(1) if m else Path(path).stem


def _volume(locator: str) -> str:
    m = re.search(r"_(\d+)$", locator)
    return f"卷{int(m.group(1))}" if m else "unknown"


def _anchor(text: str, query: str, offset: int, window: int = 40) -> str:
    start = max(offset - window, 0)
    end = min(offset + len(query) + window, len(text))
    return text[start:end].replace("\n", " ")


def _paragraph_index(text: str, offset: int) -> int:
    return len([p for p in text[:offset].split("\n\n") if p.strip()])


def _rel_source(path: str) -> str:
    marker = "/古籍/"
    normalized = path.replace("\\", "/")
    if marker in normalized:
        return normalized.split(marker, 1)[1].join(["古籍/", ""])
    return normalized


def _write_card(path: Path, meta: dict[str, Any], body: str) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is required to write candidate cards")
    path.write_text("---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n" + body, encoding="utf-8")


def generate_candidate_cards(query: str, book_id: str, out_dir: Path, *, base_url: str | None = None) -> dict[str, Any]:
    retriever = KBSearchRetriever(base_url=base_url)
    meta = retriever.get_upstream_meta()
    variants = retriever._query_variants(query)
    hits, _stats = retriever._scan_primary_files(query, book_id=book_id, mode="evidence", limit=20, query_variants=variants)
    hits = sorted(hits, key=lambda h: 0 if h.get("card_type") == "fenjuan" else 1)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "candidate_manifest.json"
    manifest = load_candidate_manifest(manifest_path) if manifest_path.exists() else new_candidate_manifest(book_id, base_corpus_version=meta.get("corpus_version", "unknown"), base_ingest_run_id=meta.get("ingest_run_id", "unknown"))
    generated = []
    for hit in hits:
        source_path = Path(str(hit.get("path")))
        if not source_path.exists():
            continue
        text = source_path.read_text(encoding="utf-8", errors="ignore")
        compact_text = text.replace(" ", "")
        match_term = next((v for v in variants if v.replace(" ", "") in compact_text), query)
        offset = compact_text.find(match_term.replace(" ", ""))
        if offset < 0:
            continue
        source_locator = _source_locator(str(source_path))
        anchor_text = _anchor(text, match_term.replace(" ", ""), offset)
        content_hash = sha256_text(anchor_text)
        candidate_id = stable_candidate_id(book_id, query, source_locator, offset)
        file_name = f"{candidate_id.split(':')[1]}.{source_locator}.{offset}.md"
        card_path = out_dir / file_name
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
            "aliases": _aliases(query),
            "source_file": _rel_source(str(source_path)),
            "source_locator": source_locator,
            "source_volume": _volume(source_locator),
            "page_marker": source_locator,
            "heading_path": [str(hit.get("title") or source_locator)],
            "paragraph_index": _paragraph_index(text, offset),
            "match_type": "exact_phrase",
            "match_offset": offset,
            "anchor_text": anchor_text,
            "content_hash": content_hash,
            "base_corpus_version": meta.get("corpus_version", "unknown"),
            "base_ingest_run_id": meta.get("ingest_run_id", "unknown"),
        }
        body = f"# {query} / {_aliases(query)[0]}\n\n## 原文证据\n\n{anchor_text}\n\n## 来源\n\n- 书名：{card_meta['book_title']}\n- 卷次：{card_meta['source_volume']}\n- 文件：{card_meta['source_file']}\n- offset：{offset}\n- page_marker：{card_meta['page_marker']}\n"
        _write_card(card_path, card_meta, body)
        item = {
            "id": candidate_id,
            "file": file_name,
            "term": query,
            "source_locator": source_locator,
            "source_volume": card_meta["source_volume"],
            "match_offset": offset,
            "content_hash": content_hash,
            "anchor_text": anchor_text,
            "review_status": "pending",
            "sync_status": "pending",
        }
        merge_candidate_item(manifest, item)
        generated.append(str(card_path))
    save_candidate_manifest(manifest_path, manifest)
    return {"generated": generated, "manifest": str(manifest_path), "message": "candidate cards generated; submit to upstream Local-KB-Unified after review."}


def _retrieve_hits(base_url: str, term: str) -> list[dict[str, Any]]:
    import urllib.error
    import urllib.request
    payload = json.dumps({"query": term, "top_k": 8, "query_mode": "evidence", "literal_first": True}).encode("utf-8")
    req = urllib.request.Request(f"{base_url.rstrip('/')}/v1/retrieve", data=payload, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []
    hits = data.get("hits") or data.get("results") or []
    return hits if isinstance(hits, list) else []


def sync_upstream_status(book_id: str, candidate_root: Path, base_url: str) -> dict[str, Any]:
    retriever = KBSearchRetriever(base_url=base_url)
    upstream_meta = retriever.get_upstream_meta()
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    updated = {"merged": 0, "needs_review": 0, "pending": 0, "stale": 0}
    manifests = sorted(candidate_root.glob(f"extract_cards/{book_id}/candidate_manifest.json"))
    for manifest_path in manifests:
        manifest = load_candidate_manifest(manifest_path)
        manifest["current_upstream_corpus_version"] = upstream_meta.get("corpus_version", "unknown")
        manifest["last_synced_at"] = now
        for item in manifest.get("items", []):
            card_path = manifest_path.parent / str(item.get("file"))
            local_stale = False
            if card_path.exists() and yaml is not None:
                text = card_path.read_text(encoding="utf-8")
                try:
                    _, fm, body = text.split("---", 2)
                    card_meta = yaml.safe_load(fm) or {}
                    source_value = str(card_meta.get("source_file") or "")
                    source_candidates = [Path(source_value), Path(retriever.settings.kb_sources_root) / source_value]
                    source_file = next((candidate for candidate in source_candidates if candidate.exists()), None)
                    if source_value and source_file is None:
                        local_stale = True
                    elif source_file is not None:
                        source_text = source_file.read_text(encoding="utf-8", errors="ignore")
                        anchor_compact = "".join(str(item.get("anchor_text") or "").split())
                        if anchor_compact and anchor_compact not in "".join(source_text.split()):
                            local_stale = True
                except Exception:
                    pass
            else:
                local_stale = True
            if local_stale:
                item["sync_status"] = "stale"
            else:
                hits = _retrieve_hits(base_url, str(item.get("term") or ""))
                same_hash = any(h.get("content_hash") == item.get("content_hash") or (isinstance(h.get("metadata"), dict) and h["metadata"].get("content_hash") == item.get("content_hash")) for h in hits)
                anchor = str(item.get("anchor_text") or "")
                strong_anchor = bool(anchor) and any(anchor in str(h.get("snippet") or h.get("anchor_text") or h.get("text") or h.get("content") or "") for h in hits)
                if same_hash or strong_anchor:
                    item["sync_status"] = "merged"
                elif hits:
                    item["sync_status"] = "needs_review"
                else:
                    item["sync_status"] = "pending"
            updated[item["sync_status"]] += 1
        save_candidate_manifest(manifest_path, manifest)
    return {"book_id": book_id, "upstream_meta": upstream_meta, "manifests": [str(p) for p in manifests], "updated": updated}
