#!/usr/bin/env python3
"""Verify a Kaiyuan release evidence archive index fully offline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from release_evidence_archive import MAX_INDEX_BYTES, ReleaseEvidenceArchiveError, verify_archive_index  # noqa: E402
from release_evidence_bundle import MAX_BUNDLE_BYTES  # noqa: E402
from scripts.create_release_evidence_archive import SafeArgumentParser, _bindings, _read_bounded, _read_bundles  # noqa: E402


def main() -> int:
    parser = SafeArgumentParser(description="Verify a Kaiyuan release evidence archive index offline")
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--bundle", required=True, action="append")
    try:
        args = parser.parse_args()
        paths = _bindings(args.bundle)
        index_bytes = _read_bounded(args.index, limit=MAX_INDEX_BYTES, field="index")
        summary = verify_archive_index(index_bytes=index_bytes, bundles=_read_bundles(paths))
    except ReleaseEvidenceArchiveError as exc:
        input_codes = {"invalid_arguments", "invalid_bundle_binding", "input_read_failed", "input_too_large"}
        prefix = "input" if exc.code in input_codes else "verification"
        print(f"release evidence archive {prefix} error: {exc.code}:{exc.field}", file=sys.stderr)
        return 2 if exc.code in input_codes else 1
    summary = dict(summary)
    summary["index_sha256"] = "sha256:" + hashlib.sha256(index_bytes).hexdigest()
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
