from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from kb_text_core import normalize_search_text

from src.connectors.evidence_resolver import resolve_evidence
from src.connectors.kb_contract import infer_metadata_from_path, is_citable_evidence
from src.connectors.primary_passage_cache import primary_passage_cache

PRIMARY_CARD_TYPES = {"fenjuan", "fulltext"}


def _load_primary_passages(kb_root: Path) -> tuple[list[Any], str]:
    root = kb_root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError("kb_root must be an existing directory")
    passages: list[Any] = []
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.md"), key=lambda item: item.as_posix()):
        inferred = infer_metadata_from_path(str(path))
        card_type = str(inferred.get("card_type") or "")
        if card_type not in PRIMARY_CARD_TYPES:
            continue
        snapshot = primary_passage_cache.load(
            path,
            card_type=card_type,
            kb_book_id=str(inferred.get("kb_book_id") or "kaiyuan_zhanjing"),
            book_title=str(inferred.get("book_title") or "唐開元占經"),
        )
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(snapshot.text.encode("utf-8"))
        passages.extend(snapshot.passages)
    if not passages:
        raise ValueError("kb_root contains no recognized primary passages")
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
        if "evidence" not in rule:
            details.append({**base, "status": "missing_evidence", "reason": "rule_has_no_evidence"})
            continue
        if not isinstance(evidence, dict):
            details.append({**base, "status": "invalid_rule", "reason": "evidence_must_be_mapping"})
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
    kb_root: str | Path,
) -> dict[str, Any]:
    source = Path(input_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    root = Path(kb_root).expanduser().resolve()
    if source == output:
        raise ValueError("output path must differ from input path")
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("output path must be outside kb_root")
    details = plan.get("details")
    if not isinstance(details, list) or len(details) != len(rules):
        raise ValueError("migration plan does not match rules")
    _, current_fingerprint = _load_primary_passages(root)
    if plan.get("source_fingerprint") != current_fingerprint:
        raise ValueError("migration plan source fingerprint is stale")
    migrated = [dict(rule) for rule in rules]
    applied_count = 0
    seen_indices: set[int] = set()
    for expected_index, detail in enumerate(details):
        if not isinstance(detail, dict):
            raise ValueError("migration plan detail must be a mapping")
        index = detail.get("rule_index")
        if index != expected_index or index in seen_indices:
            raise ValueError("migration plan rule index mismatch")
        seen_indices.add(index)
        rule = rules[index]
        expected_id = rule.get("id") if isinstance(rule, dict) else None
        if detail.get("rule_id") != expected_id:
            raise ValueError("migration plan rule id mismatch")
        before = rule.get("evidence") if isinstance(rule, dict) else None
        if detail.get("before") != before:
            raise ValueError("migration plan before evidence mismatch")
        if detail.get("status") != "migratable":
            if detail.get("after") is not None:
                raise ValueError("non-migratable plan item must not contain after")
            continue
        after = detail.get("after")
        if not isinstance(after, dict):
            raise ValueError("invalid migratable plan item")
        if not is_citable_evidence(resolve_evidence(after, root)):
            raise ValueError("planned evidence is not currently citable")
        migrated[index] = dict(migrated[index])
        migrated[index]["evidence"] = dict(after)
        applied_count += 1
    _atomic_json_write(output, migrated)
    return {"applied": True, "applied_count": applied_count, "output_path": str(output)}


def _atomic_json_write(output: Path, value: Any) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
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


def write_migration_plan(
    plan: dict[str, Any],
    *,
    input_path: str | Path,
    output_path: str | Path,
    kb_root: str | Path,
) -> None:
    source = Path(input_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    root = Path(kb_root).expanduser().resolve()
    if source == output:
        raise ValueError("plan output path must differ from input path")
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("plan output path must be outside kb_root")
    _atomic_json_write(output, plan)
