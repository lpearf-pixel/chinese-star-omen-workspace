#!/usr/bin/env python3
"""Create one deterministic index for verified release evidence bundles."""

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

from release_evidence_archive import (  # noqa: E402
    NAME_RE,
    ReleaseEvidenceArchiveError,
    build_archive_index,
    canonical_index_bytes,
)
from release_evidence_bundle import MAX_BUNDLE_BYTES  # noqa: E402


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ReleaseEvidenceArchiveError("invalid_arguments", "arguments")


def _bindings(values: list[str]) -> dict[str, Path]:
    result = {}
    for value in values:
        name, separator, raw_path = value.partition("=")
        if not separator or not raw_path or NAME_RE.fullmatch(name) is None or name in result:
            raise ReleaseEvidenceArchiveError("invalid_bundle_binding", "bundle")
        result[name] = Path(raw_path)
    return result


def _read_bundles(paths: dict[str, Path]) -> dict[str, bytes]:
    result = {}
    for name, path in paths.items():
        result[name] = _read_bounded(path, limit=MAX_BUNDLE_BYTES, field="bundle")
    return result


def _read_bounded(path: Path, *, limit: int, field: str) -> bytes:
    try:
        with path.open("rb") as handle:
            data = handle.read(limit + 1)
    except (OSError, ValueError) as exc:
        raise ReleaseEvidenceArchiveError("input_read_failed", field) from exc
    if len(data) > limit:
        raise ReleaseEvidenceArchiveError("input_too_large", field)
    return data


def _write_new_atomic(path: Path, data: bytes) -> None:
    temporary = None
    linking = False
    try:
        if path.exists():
            raise ReleaseEvidenceArchiveError("output_exists", "out")
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        linking = True
        os.link(temporary, path)
    except FileExistsError as exc:
        raise ReleaseEvidenceArchiveError("output_exists" if linking else "output_write_failed", "out") from exc
    except ReleaseEvidenceArchiveError:
        raise
    except OSError as exc:
        raise ReleaseEvidenceArchiveError("output_write_failed", "out") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = SafeArgumentParser(description="Create a verified Kaiyuan release evidence archive index")
    parser.add_argument("--bundle", required=True, action="append")
    parser.add_argument("--keep-latest", required=True, type=int)
    parser.add_argument("--pin", action="append", default=[])
    parser.add_argument("--out", required=True, type=Path)
    try:
        args = parser.parse_args()
        bundles = _read_bundles(_bindings(args.bundle))
        index = build_archive_index(bundles=bundles, keep_latest=args.keep_latest, pinned_hashes=args.pin)
        encoded = canonical_index_bytes(index)
        _write_new_atomic(args.out, encoded)
    except ReleaseEvidenceArchiveError as exc:
        print(f"release evidence archive input error: {exc.code}:{exc.field}", file=sys.stderr)
        semantic = {"bundle_verification_failed", "duplicate_bundle_hash", "unknown_pin"}
        return 1 if exc.code in semantic else 2
    classifications = {"retain": 0, "cold_archive_eligible": 0}
    for entry in index["entries"]:
        classifications[entry["classification"]] += 1
    print(
        json.dumps(
            {
                "schema_version": index["schema_version"],
                "status": "created",
                "bundle_count": len(index["entries"]),
                "retain_count": classifications["retain"],
                "cold_archive_eligible_count": classifications["cold_archive_eligible"],
                "index_sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(),
            },
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
