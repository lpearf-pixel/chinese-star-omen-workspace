from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from kb_text_core import normalize_search_text, parse_kaiyuan_passages

from src.connectors.evidence_resolver import resolve_evidence
from src.connectors.kb_contract import infer_metadata_from_path, is_citable_evidence

PRIMARY_CARD_TYPES = {"fenjuan", "fulltext"}


def _load_primary_passages(kb_root: Path) -> tuple[list[Any], str]:
    root = kb_root.expanduser().resolve()
    passages: list[Any] = []
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.md"), key=lambda item: item.as_posix()):
        inferred = infer_metadata_from_path(str(path))
        card_type = str(inferred.get("card_type") or "")
        if card_type not in PRIMARY_CARD_TYPES:
            continue
        raw = path.read_bytes()
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(raw)
        text = raw.decode("utf-8", errors="strict")
        passages.extend(
            parse_kaiyuan_passages(
                text,
                source_path=str(path.resolve()),
                card_type=card_type,
                kb_book_id=str(inferred.get("kb_book_id") or "kaiyuan_zhanjing"),
                book_title=str(inferred.get("book_title") or "唐開元占經"),
            )
        )
    return passages, "sha256:" + digest.hexdigest()


def _candidate_trace(passage: Any, root: Path) -> dict[str, Any]:
    source = Path(passage.source_path).resolve()
    return {
        "relative_path": source.relative_to(root).as_posix(),
        "card_type": passage.card_type,
        "source_locator": passage.source_locator,
        "page_marker": passage.page_marker,
        "paragraph_index": passage.paragraph_index,
        "heading_path": list(passage.heading_path),
        "raw_start": passage.raw_start,
        "raw_end": passage.raw_end,
        "raw_content_hash": passage.raw_content_hash,
        "normalized_content_hash": passage.normalized_content_hash,
    }


def plan_rule_evidence_migration(
    rules: list[dict[str, Any]],
    *,
    kb_root: str | Path,
) -> dict[str, Any]:
    if not isinstance(rules, list):
        raise ValueError("rules must be a JSON array")
    root = Path(kb_root).expanduser().resolve()
    passages, source_fingerprint = _load_primary_passages(root)
    seen: set[str] = set()
    details: list[dict[str, Any]] = []

    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            details.append(
                {
                    "rule_id": None,
                    "rule_index": index,
                    "status": "invalid_rule",
                    "reason": "rule_must_be_mapping",
                    "before": None,
                    "after": None,
                    "match_type": None,
                    "validation_status": None,
                    "candidates": [],
                }
            )
            continue
        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            details.append(
                {
                    "rule_id": None,
                    "rule_index": index,
                    "status": "invalid_rule",
                    "reason": "rule_id_must_be_nonempty_string",
                    "before": rule.get("evidence"),
                    "after": None,
                    "match_type": None,
                    "validation_status": None,
                    "candidates": [],
                }
            )
            continue
        rule_id = rule_id.strip()
        if rule_id in seen:
            raise ValueError(f"duplicate rule id {rule_id!r}")
        seen.add(rule_id)
        evidence = rule.get("evidence")
        base = {
            "rule_id": rule_id,
            "rule_index": index,
            "before": evidence,
            "after": None,
            "match_type": None,
            "validation_status": None,
            "candidates": [],
        }
        if not isinstance(evidence, dict):
            details.append({**base, "status": "missing_evidence", "reason": "rule_has_no_evidence"})
            continue
        resolved = resolve_evidence(evidence, root)
        if is_citable_evidence(resolved):
            details.append(
                {
                    **base,
                    "status": "already_citable",
                    "reason": None,
                    "validation_status": "citable",
                }
            )
            continue
        card_type = str(evidence.get("card_type") or "")
        anchor = evidence.get("anchor_text") or evidence.get("quote")
        if card_type not in PRIMARY_CARD_TYPES or not isinstance(anchor, str) or not anchor:
            reason = "card_type_not_primary" if card_type not in PRIMARY_CARD_TYPES else "missing_anchor"
            details.append({**base, "status": "candidate_only", "reason": reason})
            continue

        matching = [passage for passage in passages if anchor in passage.raw_text]
        match_type = "exact_raw"
        if not matching:
            normalized = normalize_search_text(anchor)
            matching = [
                passage
                for passage in passages
                if normalized and normalized in passage.normalized_text
            ]
            match_type = "exact_normalized"
        candidates = [_candidate_trace(item, root) for item in matching]
        if not matching:
            details.append({**base, "status": "unresolved", "reason": "no_exact_primary_match"})
            continue
        if len(matching) != 1:
            details.append(
                {
                    **base,
                    "status": "ambiguous",
                    "reason": "multiple_exact_primary_matches",
                    "match_type": match_type,
                    "candidates": candidates,
                }
            )
            continue

        passage = matching[0]
        trace = candidates[0]
        after = dict(evidence)
        after.update(
            {
                "kb_book_id": passage.kb_book_id,
                "relative_path": trace["relative_path"],
                "card_type": passage.card_type,
                "source_locator": passage.source_locator,
                "page_marker": passage.page_marker,
                "paragraph_index": passage.paragraph_index,
                "heading_path": list(passage.heading_path),
                "anchor_text": anchor,
                "raw_content_hash": passage.raw_content_hash,
                "normalized_content_hash": passage.normalized_content_hash,
            }
        )
        validated = resolve_evidence(after, root)
        validation_status = str(validated.get("status") or "unknown")
        if not is_citable_evidence(validated):
            details.append(
                {
                    **base,
                    "status": "unresolved",
                    "reason": "migration_validation_failed",
                    "match_type": match_type,
                    "validation_status": validation_status,
                    "candidates": candidates,
                }
            )
            continue
        details.append(
            {
                **base,
                "status": "migratable",
                "reason": None,
                "after": after,
                "match_type": match_type,
                "validation_status": validation_status,
                "candidates": candidates,
            }
        )

    counts: dict[str, int] = {}
    for detail in details:
        status = detail["status"]
        counts[status] = counts.get(status, 0) + 1
    return {
        "total_rules": len(rules),
        "source_fingerprint": source_fingerprint,
        "status_counts": dict(sorted(counts.items())),
        "details": details,
        "applied": False,
    }


def apply_rule_evidence_migration(
    *,
    rules: list[dict[str, Any]],
    plan: dict[str, Any],
    input_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    source = Path(input_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    if source == output:
        raise ValueError("output path must differ from input path")
    details = plan.get("details")
    if not isinstance(details, list) or len(details) != len(rules):
        raise ValueError("migration plan does not match rules")
    migrated = [dict(rule) for rule in rules]
    applied_count = 0
    for detail in details:
        if detail.get("status") != "migratable":
            continue
        index = detail.get("rule_index")
        after = detail.get("after")
        if not isinstance(index, int) or not isinstance(after, dict):
            raise ValueError("invalid migratable plan item")
        migrated[index] = dict(migrated[index])
        migrated[index]["evidence"] = dict(after)
        applied_count += 1
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(migrated, ensure_ascii=False, indent=2) + "\n"
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, output)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return {"applied": True, "applied_count": applied_count, "output_path": str(output)}
