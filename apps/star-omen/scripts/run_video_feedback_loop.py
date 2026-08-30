#!/usr/bin/env python3
"""Build and atomically publish one offline feedback-loop S0 package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pydantic import ValidationError

from src.video_pipeline.contracts import ExternalAuditBundleV1
from src.video_pipeline.feedback_loop.contracts_v1 import (
    FeedbackOutcomeV1,
    LocalEvidenceProbeV1,
)
from src.video_pipeline.feedback_loop.orchestrator import (
    build_feedback_loop_run,
    publish_feedback_loop_run,
)


class FeedbackLoopCliError(ValueError):
    """An actionable local input error."""


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FeedbackLoopCliError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise FeedbackLoopCliError(f"non-finite JSON value: {value}")


def _load_strict_json(path: Path, *, label: str) -> object:
    try:
        raw = path.read_text(encoding="utf-8")
        return json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FeedbackLoopCliError(f"{label} JSON is invalid: {exc}") from exc


def _load_audit(path: Path) -> ExternalAuditBundleV1:
    payload = _load_strict_json(path, label="audit")
    if not isinstance(payload, dict):
        raise FeedbackLoopCliError("audit JSON must contain one object")
    return ExternalAuditBundleV1.model_validate(payload)


def _load_probes(path: Path) -> tuple[LocalEvidenceProbeV1, ...]:
    payload = _load_strict_json(path, label="probes")
    if not isinstance(payload, list):
        raise FeedbackLoopCliError("probes JSON must contain one array")
    return tuple(LocalEvidenceProbeV1.model_validate(item) for item in payload)


def _load_outcome(path: Path) -> FeedbackOutcomeV1:
    payload = _load_strict_json(path, label="outcome")
    if not isinstance(payload, dict):
        raise FeedbackLoopCliError("outcome JSON must contain one object")
    return FeedbackOutcomeV1.model_validate(payload)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build one deterministic offline evidence-to-video feedback run."
    )
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--probes", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--outcome", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        audit = _load_audit(args.audit)
        probes = _load_probes(args.probes)
        outcome = _load_outcome(args.outcome) if args.outcome is not None else None
        build = build_feedback_loop_run(
            audit_bundle=audit,
            local_probes=probes,
            outcome=outcome,
        )
        published = publish_feedback_loop_run(output_dir=args.output, build=build)
    except FileExistsError:
        print(
            f"error: output destination already exists: {args.output}",
            file=sys.stderr,
        )
        return 1
    except (FeedbackLoopCliError, OSError, ValidationError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(published)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
