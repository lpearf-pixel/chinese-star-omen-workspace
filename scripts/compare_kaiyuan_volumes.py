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
    parser = argparse.ArgumentParser(description="Compare derived Kaiyuan volumes with the combined immutable fulltext.")
    parser.add_argument("--fulltext", type=Path, default=DEFAULT_ROOT / "唐開元占經-全文合併版.md")
    parser.add_argument("--volumes-dir", type=Path, default=DEFAULT_ROOT / "分卷")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    audit = audit_kaiyuan_corpus(args.fulltext, args.volumes_dir)
    report = {
        "schema_version": "kaiyuan-volume-compare/v1",
        "fulltext": str(args.fulltext),
        "volumes_dir": str(args.volumes_dir),
        "byte_equal_count": audit["byte_equal_count"],
        "whitespace_only_count": audit["whitespace_only_count"],
        "substantive_difference_count": audit["substantive_difference_count"],
        "missing_volume_files": audit["missing_volume_files"],
        "extra_volume_files": audit["extra_volume_files"],
        "different_volumes": audit["different_volumes"],
        "comparisons": audit["comparisons"],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")

    if args.strict and (
        report["missing_volume_files"]
        or report["extra_volume_files"]
        or report["different_volumes"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
