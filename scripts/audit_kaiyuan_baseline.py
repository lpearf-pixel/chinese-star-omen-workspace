#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEXT_CORE = ROOT / "packages" / "kb-text-core" / "python"
if str(TEXT_CORE) not in sys.path:
    sys.path.insert(0, str(TEXT_CORE))

from kb_text_core import audit_kaiyuan_corpus  # noqa: E402

BASELINE_FIELDS = (
    "fulltext_sha256",
    "section_count",
    "page_marker_count",
    "kr_entity_count",
    "replacement_character_count",
)


def compare_baseline(
    audit: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}
    for field in BASELINE_FIELDS:
        expected = baseline.get(field)
        actual = audit.get(field)
        checks[field] = {
            "expected": expected,
            "actual": actual,
            "match": expected == actual,
        }

    expected_volume_count = baseline.get("volume_file_count")
    actual_volume_count = (
        int(audit.get("expected_section_count") or 0)
        - len(audit.get("missing_volume_files") or [])
        + len(audit.get("extra_volume_files") or [])
    )
    checks["volume_file_count"] = {
        "expected": expected_volume_count,
        "actual": actual_volume_count,
        "match": expected_volume_count == actual_volume_count,
    }

    return {
        "schema_version": "kaiyuan-corpus-baseline-check/v1",
        "book_id": baseline.get("book_id"),
        "audit_ok": bool(audit.get("ok")),
        "baseline_matches": all(check["match"] for check in checks.values()),
        "checks": checks,
        "audit": audit,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the Kaiyuan corpus and verify the immutable baseline metrics."
    )
    parser.add_argument("--fulltext", type=Path, required=True)
    parser.add_argument("--volumes-dir", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    for path, label in (
        (args.fulltext, "fulltext"),
        (args.baseline, "baseline"),
    ):
        if not path.is_file():
            parser.error(f"{label} file not found: {path}")
    if not args.volumes_dir.is_dir():
        parser.error(f"volumes directory not found: {args.volumes_dir}")

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    audit = audit_kaiyuan_corpus(args.fulltext, args.volumes_dir)
    report = compare_baseline(audit, baseline)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["audit_ok"] and report["baseline_matches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
