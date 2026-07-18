#!/usr/bin/env python3
"""Validate a recorded Kaiyuan release/rollback drill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from release_drill import validate_release_drill  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a non-mutating Kaiyuan release rollback drill")
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("input root must be an object")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"release drill input error: {exc}", file=sys.stderr)
        return 2

    report = validate_release_drill(document)
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
