#!/usr/bin/env python3
"""Assemble strict B7 observations into one validated B6 input artifact."""

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

from release_artifact import ReleaseArtifactError, assemble_release_artifact  # noqa: E402


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ReleaseArtifactError("invalid_arguments", "arguments")


def _reject_constant(value: str):
    raise ValueError("non-finite token")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _load_strict_json(path: Path, field: str):
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_constant,
            object_pairs_hook=_unique_object,
        )
        _require_bounded_json(value)
        return value
    except (OSError, UnicodeError) as exc:
        raise ReleaseArtifactError("input_read_failed", field) from exc
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise ReleaseArtifactError("invalid_json", field) from exc


def _require_bounded_json(value, *, max_depth: int = 128, max_nodes: int = 100_000) -> None:
    pending = [(value, 0)]
    visited = 0
    while pending:
        item, depth = pending.pop()
        visited += 1
        if depth > max_depth or visited > max_nodes:
            raise ValueError("JSON structure exceeds safety limit")
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)


def _write_new_atomic(path: Path, document: dict[str, object]) -> bytes:
    temporary = None
    linking = False
    try:
        if path.exists():
            raise ReleaseArtifactError("output_exists", "out")
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = (json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        linking = True
        os.link(temporary, path)
    except FileExistsError as exc:
        code = "output_exists" if linking else "output_write_failed"
        raise ReleaseArtifactError(code, "out") from exc
    except ReleaseArtifactError:
        raise
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        raise ReleaseArtifactError("output_write_failed", "out") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return encoded


def main() -> int:
    parser = SafeArgumentParser(description="Assemble a validated Kaiyuan release drill artifact")
    parser.add_argument("--before-switch", required=True, type=Path)
    parser.add_argument("--after-switch", required=True, type=Path)
    parser.add_argument("--after-rollback", required=True, type=Path)
    parser.add_argument("--expected-manifest", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    try:
        args = parser.parse_args()
    except ReleaseArtifactError as exc:
        print(f"release artifact input error: {exc.code}:{exc.field}", file=sys.stderr)
        return 2

    fields = {
        "before_switch": args.before_switch,
        "after_switch": args.after_switch,
        "after_rollback": args.after_rollback,
    }
    try:
        observations = {name: _load_strict_json(path, name) for name, path in fields.items()}
        manifest = _load_strict_json(args.expected_manifest, "expected_manifest")
        document, report = assemble_release_artifact(
            observations=observations,
            expected_manifest=manifest,
        )
        encoded = _write_new_atomic(args.out, document)
    except ReleaseArtifactError as exc:
        if exc.code == "drill_validation_failed":
            print(json.dumps(exc.report, ensure_ascii=False, indent=2, allow_nan=False))
            print(f"release artifact validation error: {exc.code}:{exc.field}", file=sys.stderr)
            return 1
        print(f"release artifact input error: {exc.code}:{exc.field}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "status": "assembled",
                "phases": list(fields),
                "out": str(args.out),
                "artifact_sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(),
                "validation_status": report["status"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
