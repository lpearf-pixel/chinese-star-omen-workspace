#!/usr/bin/env python3
"""Create one deterministic Kaiyuan release evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from release_evidence_bundle import (  # noqa: E402
    MAX_MEMBER_BYTES,
    ReleaseEvidenceBundleError,
    create_bundle_bytes,
    load_strict_json_bytes,
)


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ReleaseEvidenceBundleError("invalid_arguments", "arguments")


def _load(path: Path, field: str):
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ReleaseEvidenceBundleError("input_read_failed", field) from exc
    if len(data) > MAX_MEMBER_BYTES:
        raise ReleaseEvidenceBundleError("input_too_large", field)
    try:
        return load_strict_json_bytes(data, field)
    except ReleaseEvidenceBundleError as exc:
        raise ReleaseEvidenceBundleError("invalid_json", field) from exc


def _write_new_atomic(path: Path, data: bytes) -> None:
    temporary = None
    linking = False
    try:
        if path.exists():
            raise ReleaseEvidenceBundleError("output_exists", "out")
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        linking = True
        os.link(temporary, path)
    except FileExistsError as exc:
        raise ReleaseEvidenceBundleError("output_exists" if linking else "output_write_failed", "out") from exc
    except ReleaseEvidenceBundleError:
        raise
    except OSError as exc:
        raise ReleaseEvidenceBundleError("output_write_failed", "out") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = SafeArgumentParser(description="Create a sealed Kaiyuan release evidence bundle")
    parser.add_argument("--before-switch", required=True, type=Path)
    parser.add_argument("--after-switch", required=True, type=Path)
    parser.add_argument("--after-rollback", required=True, type=Path)
    parser.add_argument("--expected-manifest", required=True, type=Path)
    parser.add_argument("--assembled-input", required=True, type=Path)
    parser.add_argument("--release-head", required=True)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--out", required=True, type=Path)
    try:
        args = parser.parse_args()
        observations = {
            "before_switch": _load(args.before_switch, "before_switch"),
            "after_switch": _load(args.after_switch, "after_switch"),
            "after_rollback": _load(args.after_rollback, "after_rollback"),
        }
        data, summary = create_bundle_bytes(
            observations=observations,
            expected_manifest=_load(args.expected_manifest, "expected_manifest"),
            assembled_document=_load(args.assembled_input, "assembled_input"),
            release_head=args.release_head,
            created_at=args.created_at,
        )
        _write_new_atomic(args.out, data)
    except ReleaseEvidenceBundleError as exc:
        print(f"release evidence bundle input error: {exc.code}:{exc.field}", file=sys.stderr)
        return 1 if exc.code in {"assembly_mismatch", "drill_validation_failed"} else 2
    summary = dict(summary)
    summary["bundle_sha256"] = "sha256:" + hashlib.sha256(data).hexdigest()
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
