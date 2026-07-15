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

from kb_text_core import split_kaiyuan_fulltext, write_split_volumes  # noqa: E402

DEFAULT_ROOT = ROOT / "apps" / "local-kb-unified" / "data" / "sources" / "古籍" / "唐開元占經"


def main() -> int:
    parser = argparse.ArgumentParser(description="Split the immutable Kaiyuan combined text into a separate output directory.")
    parser.add_argument("--fulltext", type=Path, default=DEFAULT_ROOT / "唐開元占經-全文合併版.md")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--write", action="store_true", help="Write files; without this flag the command is a dry run")
    parser.add_argument("--force", action="store_true", help="Allow overwriting files in the explicit output directory")
    args = parser.parse_args()

    sections = split_kaiyuan_fulltext(args.fulltext.read_text(encoding="utf-8"))
    if not args.write:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "section_count": len(sections),
                    "out_dir": str(args.out_dir),
                    "would_write": ["%s.md" % locator for locator in sorted(sections)],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    result = write_split_volumes(args.fulltext, args.out_dir, force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
