#!/usr/bin/env python3
"""Offline verification for one Kaiyuan release evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from release_evidence_bundle import MAX_BUNDLE_BYTES, ReleaseEvidenceBundleError, verify_bundle_bytes  # noqa: E402


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ReleaseEvidenceBundleError("invalid_arguments", "arguments")


def main() -> int:
    parser = SafeArgumentParser(description="Verify a sealed Kaiyuan release evidence bundle offline")
    parser.add_argument("--bundle", required=True, type=Path)
    try:
        args = parser.parse_args()
        data = args.bundle.read_bytes()
        if len(data) > MAX_BUNDLE_BYTES:
            raise ReleaseEvidenceBundleError("archive_contract_error", "bundle")
        summary = verify_bundle_bytes(data)
    except OSError:
        print("release evidence bundle input error: input_read_failed:bundle", file=sys.stderr)
        return 2
    except ReleaseEvidenceBundleError as exc:
        prefix = "input" if exc.code == "invalid_arguments" else "verification"
        print(f"release evidence bundle {prefix} error: {exc.code}:{exc.field}", file=sys.stderr)
        return 2 if exc.code == "invalid_arguments" else 1
    summary = dict(summary)
    summary["bundle_sha256"] = "sha256:" + hashlib.sha256(data).hexdigest()
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
