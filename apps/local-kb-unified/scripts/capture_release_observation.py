#!/usr/bin/env python3
"""Capture one read-only Kaiyuan release observation phase."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile

from qdrant_client import QdrantClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from release_observation import ReleaseObservationError, capture_phase_observation  # noqa: E402
from release_observation_live import KBSearchReadClient, QdrantCollectionReader  # noqa: E402


def _write_new_atomic(path: Path, payload: dict) -> None:
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture a read-only Kaiyuan release observation")
    parser.add_argument("--phase", required=True, choices=("before_switch", "after_switch", "after_rollback"))
    parser.add_argument("--active-collection", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--qdrant-url", required=True)
    parser.add_argument("--api-key-env", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env, "").strip()
    if not api_key:
        print("release observation input error: missing_api_key", file=sys.stderr)
        return 2
    if args.out.exists():
        print("release observation input error: output_exists", file=sys.stderr)
        return 2

    kb = KBSearchReadClient(
        base_url=args.base_url,
        api_key=api_key,
        timeout_seconds=args.timeout,
    )
    qdrant = QdrantCollectionReader(QdrantClient(url=args.qdrant_url, timeout=args.timeout))
    try:
        observation = capture_phase_observation(
            active_collection=args.active_collection,
            query=args.query,
            fetch_health=kb.health,
            fetch_meta=kb.meta,
            retrieve=kb.retrieve,
            inspect_collection=qdrant.inspect,
            captured_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        observation["phase_name"] = args.phase
        _write_new_atomic(args.out, observation)
    except ReleaseObservationError as exc:
        print(f"release observation error: {exc.code}:{exc.operation}", file=sys.stderr)
        return 1
    except (FileExistsError, OSError, TypeError, ValueError):
        print("release observation input error: output_write_failed", file=sys.stderr)
        return 2
    print(json.dumps({"status": "captured", "phase": args.phase, "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
