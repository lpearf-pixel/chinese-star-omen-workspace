#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_CORE = ROOT / "packages" / "kb-text-core" / "python"
if str(TEXT_CORE) not in sys.path:
    sys.path.insert(0, str(TEXT_CORE))

from kb_text_core import audit_kaiyuan_corpus  # noqa: E402


FAIL_FIELDS = (
    "missing_sections",
    "extra_sections",
    "missing_volume_files",
    "extra_volume_files",
    "different_volumes",
    "duplicate_page_markers",
    "invalid_page_markers",
    "page_marker_volume_mismatches",
    "non_monotonic_page_markers",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the immutable Kaiyuan fulltext against derived volume files.")
    parser.add_argument("--fulltext", type=Path, required=True)
    parser.add_argument("--volumes-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = audit_kaiyuan_corpus(args.fulltext, args.volumes_dir)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    failed = any(report.get(field) for field in FAIL_FIELDS)
    failed = failed or report.get("section_count") != report.get("expected_section_count")
    failed = failed or bool(report.get("replacement_character_count"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
