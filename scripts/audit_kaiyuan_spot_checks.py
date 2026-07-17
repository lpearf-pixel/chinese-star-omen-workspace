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

from kb_text_core import audit_ctext_spot_checks  # noqa: E402

DEFAULT_CONFIG = ROOT / "corpus" / "kaiyuan_zhanjing" / "ctext_spot_checks.json"
DEFAULT_CORPUS_ROOT = (
    ROOT
    / "apps"
    / "local-kb-unified"
    / "data"
    / "sources"
    / "古籍"
    / "唐開元占經"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare manually supplied CText reference excerpts with local "
            "Kaiyuan files. This command performs no network access."
        )
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when any configured check is not exact_raw/exact_normalized",
    )
    args = parser.parse_args()

    if not args.config.is_file():
        parser.error(f"spot-check config not found: {args.config}")
    if not args.corpus_root.is_dir():
        parser.error(f"corpus root not found: {args.corpus_root}")

    report = audit_ctext_spot_checks(args.config, args.corpus_root)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.out.with_suffix(args.out.suffix + ".tmp")
        temporary.write_text(rendered, encoding="utf-8")
        temporary.replace(args.out)
    print(rendered, end="")
    return 1 if args.strict and not report["all_matched"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
