from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "kb-contracts" / "python"
sys.path.insert(0, str(CONTRACTS))
from kb_contracts import REVIEW_STATUSES, SYNC_STATUSES, load_candidate_manifest, sha256_text, stable_candidate_id  # noqa: E402

REQUIRED = [
    "schema_version", "kb_book_id", "book_title", "card_type", "evidence_level",
    "source_namespace", "generated_by", "generated_status", "review_status", "sync_status",
    "term", "aliases", "source_file", "source_locator", "source_volume", "page_marker",
    "heading_path", "paragraph_index", "match_type", "match_offset", "anchor_text",
    "content_hash", "base_corpus_version", "base_ingest_run_id",
]
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise ValueError("markdown candidate card must start with YAML frontmatter delimiter '---'")
    try:
        _, fm, body = text.split("---", 2)
    except ValueError as exc:
        raise ValueError("markdown candidate card has unterminated YAML frontmatter") from exc
    if yaml is None:
        raise RuntimeError("PyYAML is required to parse candidate frontmatter")
    data = yaml.safe_load(fm) or {}
    if not isinstance(data, dict):
        raise ValueError("candidate frontmatter must be a mapping")
    return data, body.lstrip("\n")


def dump_frontmatter(meta: dict[str, Any], body: str) -> str:
    if yaml is None:
        raise RuntimeError("PyYAML is required to write candidate frontmatter")
    return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n" + body.lstrip("\n")


def validate_meta(meta: dict[str, Any], *, book_id: str) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in meta:
            errors.append(f"missing required frontmatter field: {key}")
    checks = {
        "schema_version": "candidate-card/v1",
        "kb_book_id": book_id,
        "card_type": "extract_card",
        "evidence_level": "candidate",
        "source_namespace": "downstream_generated",
    }
    for key, expected in checks.items():
        if meta.get(key) != expected:
            errors.append(f"{key} must be {expected!r}, got {meta.get(key)!r}")
    if meta.get("review_status") not in REVIEW_STATUSES:
        errors.append(f"review_status must be one of {sorted(REVIEW_STATUSES)}")
    if meta.get("sync_status") not in SYNC_STATUSES:
        errors.append(f"sync_status must be one of {sorted(SYNC_STATUSES)}")
    if not HASH_RE.match(str(meta.get("content_hash") or "")):
        errors.append("content_hash must match sha256:<64 lowercase hex chars>")
    return errors


def load_inbox(inbox: Path, book_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = load_candidate_manifest(inbox / "candidate_manifest.json")
    if manifest.get("book_id") != book_id:
        raise ValueError(f"manifest book_id {manifest.get('book_id')!r} does not match --book-id {book_id!r}")
    cards: list[dict[str, Any]] = []
    for item in manifest.get("items", []):
        rel = item.get("file")
        if not rel:
            raise ValueError(f"manifest item missing file: {item}")
        path = inbox / rel
        if not path.exists():
            raise FileNotFoundError(f"manifest item file not found: {path}")
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        cards.append({"item": item, "path": path, "meta": meta, "body": body})
    return manifest, cards


def validate_card(card: dict[str, Any], *, book_id: str) -> list[str]:
    errors = validate_meta(card["meta"], book_id=book_id)
    meta = card["meta"]
    item = card["item"]
    if not errors:
        expected_id = stable_candidate_id(meta["kb_book_id"], meta["term"], meta["source_locator"], meta["match_offset"])
        if item.get("id") != expected_id:
            errors.append(f"manifest item id must be stable candidate id {expected_id!r}, got {item.get('id')!r}")
        for key in ["term", "source_locator", "source_volume", "match_offset", "content_hash", "anchor_text", "review_status", "sync_status"]:
            if item.get(key) != meta.get(key):
                errors.append(f"manifest item field {key!r} must match card frontmatter")
        expected_hash = sha256_text(str(meta.get("anchor_text") or ""))
        if meta.get("content_hash") != expected_hash:
            errors.append(f"content_hash must equal sha256_text(anchor_text): expected {expected_hash}")
    return errors


def validate_mode(inbox: Path, book_id: str) -> int:
    _, cards = load_inbox(inbox, book_id)
    report = {"mode": "validate", "inbox": str(inbox), "book_id": book_id, "checked": len(cards), "ok": 0, "errors": []}
    for card in cards:
        errors = validate_card(card, book_id=book_id)
        if errors:
            report["errors"].append({"file": card["path"].name, "errors": errors})
        else:
            report["ok"] += 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not report["errors"] else 1


def promote_mode(inbox: Path, book_id: str) -> int:
    manifest, cards = load_inbox(inbox, book_id)
    dest = Path("data/generated/extract_cards") / book_id
    dest.mkdir(parents=True, exist_ok=True)
    promoted: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for card in cards:
        errors = validate_card(card, book_id=book_id)
        if errors:
            raise ValueError(f"cannot promote invalid candidate {card['path']}: {errors}")
        meta = dict(card["meta"])
        if meta.get("review_status") != "approved" or meta.get("sync_status") in {"stale"}:
            skipped.append({"file": card["path"].name, "review_status": str(meta.get("review_status")), "sync_status": str(meta.get("sync_status"))})
            continue
        meta["evidence_level"] = "primary"
        meta["source_namespace"] = "official"
        meta["generated_status"] = "promoted"
        meta["review_status"] = "approved"
        out_path = dest / card["path"].name
        out_path.write_text(dump_frontmatter(meta, card["body"]), encoding="utf-8")
        promoted.append({**card["item"], "file": str(out_path.relative_to(Path("data/generated"))), "review_status": "approved", "sync_status": meta.get("sync_status", "pending")})
    promoted_manifest = {**manifest, "items": promoted}
    (dest / "promoted_manifest.json").write_text(json.dumps(promoted_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"mode": "promote", "promoted": len(promoted), "skipped": skipped, "destination": str(dest)}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or promote downstream candidate extract cards. Does not run ingest.")
    parser.add_argument("--inbox", required=True, type=Path, help="Inbox directory containing candidate_manifest.json and markdown cards")
    parser.add_argument("--book-id", required=True, help="Expected kb_book_id/book_id")
    parser.add_argument("--mode", required=True, choices=["validate", "promote"], help="validate reports only; promote copies approved cards into data/generated")
    args = parser.parse_args()
    if args.mode == "validate":
        return validate_mode(args.inbox, args.book_id)
    return promote_mode(args.inbox, args.book_id)


if __name__ == "__main__":
    raise SystemExit(main())
