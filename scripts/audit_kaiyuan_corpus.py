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


DEFAULT_ROOT = ROOT / "apps" / "local-kb-unified" / "data" / "sources" / "古籍" / "唐開元占經"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the immutable Kaiyuan fulltext against derived volume files.")
    parser.add_argument("--fulltext", type=Path, default=DEFAULT_ROOT / "唐開元占經-全文合併版.md")
    parser.add_argument("--volumes-dir", type=Path, default=DEFAULT_ROOT / "分卷")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--strict", action="store_true", help="Fail on corpus, volume, or page-marker integrity errors")
    args = parser.parse_args()

    report = audit_kaiyuan_corpus(args.fulltext, args.volumes_dir)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")

    failed = bool(
        report["different_volumes"]
        or report["duplicate_section_headings"]
        or report["empty_sections"]
        or report["missing_sections"]
        or report["missing_volume_files"]
        or report["extra_sections"]
        or report["extra_volume_files"]
        or report["empty_volume_files"]
        or report["replacement_character_count"]
    )
    if args.strict:
        failed = failed or bool(
            report["duplicate_page_markers"]
            or report["invalid_page_markers"]
            or report["page_marker_volume_mismatches"]
            or report["non_monotonic_page_markers"]
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
