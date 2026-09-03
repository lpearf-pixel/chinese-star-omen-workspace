#!/usr/bin/env python3
"""Build one episode-22 feedback-loop S1 package from read-only evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Callable, Mapping


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pydantic import TypeAdapter, ValidationError

from src.connectors.evidence_resolver import EvidenceResolverContext, resolve_evidence
from src.video_pipeline.contracts._common import StableId
from src.video_pipeline.feedback_loop.orchestrator import (
    build_feedback_loop_run,
    publish_feedback_loop_run,
)
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
    ReadOnlyTwoStageRetriever,
    bind_production_query_plan_to_audit,
    bind_source_snapshot_to_plan,
)
from src.video_pipeline.feedback_loop.readonly_kb_v1 import (
    build_readonly_kb_retriever,
)
from src.video_pipeline.feedback_loop.readonly_runtime_v1 import (
    build_local_evidence_probes,
)
from src.video_pipeline.feedback_loop.source_snapshot_v1 import LocalKBSourceAccessor
from src.video_pipeline.feedback_loop.strict_local_files import (
    StrictJSONDocument,
    load_external_audit_v1,
    load_query_plan_v1,
    load_source_snapshot_v1,
)


_SOURCE_ID = "media:douyin:zushan:collection-7664842437629921326:episode-22"
_AUDIT_ID = "audit:douyin:zushan:episode-22"
_WORK_ID = "7669807398794598565"
_BOOK_ID = "kaiyuan_zhanjing"
_STABLE_ID = TypeAdapter(StableId)


class SafeArgumentParser(argparse.ArgumentParser):
    """Argument parser whose failures cannot reflect caller-provided bytes."""

    def error(self, message: str) -> None:
        del message
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.INVALID_LOCAL_INPUT) from None


def _parser() -> SafeArgumentParser:
    parser = SafeArgumentParser(
        description="Build one episode-22 read-only evidence feedback run.",
        allow_abbrev=False,
        add_help=False,
    )
    parser.add_argument("--help", action="help", help=argparse.SUPPRESS)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--query-plan", required=True, type=Path)
    parser.add_argument("--kb-root", required=True, type=Path)
    parser.add_argument("--source-snapshot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def _require_episode_22_pilot(
    audit_doc: StrictJSONDocument,
    plan_doc: StrictJSONDocument,
) -> None:
    audit = audit_doc.value
    plan = plan_doc.value
    if (
        audit.source.source_id != _SOURCE_ID
        or audit.audit.audit_id != _AUDIT_ID
        or audit.source.platform_work_id != _WORK_ID
        or plan.source_id != _SOURCE_ID
        or plan.audit_id != _AUDIT_ID
        or plan.kb_book_id != _BOOK_ID
        or any(request.kb_book_id != _BOOK_ID for request in plan.requests)
    ):
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.PLAN_MISMATCH) from None


def _complete_batch_build_publish(
    *,
    audit_doc: StrictJSONDocument,
    plan_doc: StrictJSONDocument,
    snapshot_doc: StrictJSONDocument,
    kb_root: Path,
    output: Path,
    source_accessor: LocalKBSourceAccessor,
    retriever: ReadOnlyTwoStageRetriever,
    resolver_context: EvidenceResolverContext,
    resolver: Callable[..., Mapping[str, object]] = resolve_evidence,
) -> str:
    """Complete the full probe batch before performing one atomic publication."""

    probes = build_local_evidence_probes(
        audit_bundle=audit_doc.value,
        query_plan=plan_doc.value,
        plan_sha256=plan_doc.canonical_sha256,
        retriever=retriever,
        kb_root=kb_root,
        source_snapshot=snapshot_doc.value,
        source_snapshot_sha256=snapshot_doc.canonical_sha256,
        source_accessor=source_accessor,
        resolver_context=resolver_context,
        resolver=resolver,
    )
    source_accessor.assert_unchanged()
    build = build_feedback_loop_run(
        audit_bundle=audit_doc.value,
        local_probes=probes,
        outcome=None,
    )
    publish_feedback_loop_run(output_dir=output, build=build)
    return build.run.run_id


def _run_production(args: argparse.Namespace) -> str:
    audit_doc = load_external_audit_v1(args.audit)
    plan_doc = load_query_plan_v1(args.query_plan)
    snapshot_doc = load_source_snapshot_v1(args.source_snapshot)
    _require_episode_22_pilot(audit_doc, plan_doc)
    bind_production_query_plan_to_audit(
        plan=plan_doc.value,
        audit_bundle=audit_doc.value,
    )
    bind_source_snapshot_to_plan(
        snapshot=snapshot_doc.value,
        plan=plan_doc.value,
    )
    with LocalKBSourceAccessor.open(
        kb_root=args.kb_root,
        snapshot=snapshot_doc.value,
    ) as accessor:
        session = build_readonly_kb_retriever(
            kb_root=args.kb_root,
            collection=plan_doc.value.collection,
            expected_corpus_version=plan_doc.value.expected_corpus_version,
            source_accessor=accessor,
            source_snapshot=snapshot_doc.value,
            source_snapshot_sha256=snapshot_doc.canonical_sha256,
        )
        return _complete_batch_build_publish(
            audit_doc=audit_doc,
            plan_doc=plan_doc,
            snapshot_doc=snapshot_doc,
            kb_root=args.kb_root,
            output=args.output,
            source_accessor=accessor,
            retriever=session,
            resolver_context=session.resolver_context,
        )


def _validated_claim_id(error: ReadOnlyAdapterError) -> str | None:
    if error.failed_claim_id is None:
        return None
    try:
        return _STABLE_ID.validate_python(error.failed_claim_id)
    except ValidationError:
        return None


def _print_failure(error: ReadOnlyAdapterError) -> None:
    claim_id = _validated_claim_id(error)
    suffix = f" claim_id={claim_id}" if claim_id is not None else ""
    print(f"{error.code.value}{suffix}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        run_id = _run_production(args)
    except ReadOnlyAdapterError as error:
        _print_failure(error)
        return 1
    except FileExistsError:
        _print_failure(ReadOnlyAdapterError(ReadOnlyErrorCode.OUTPUT_CONFLICT))
        return 1
    except Exception:
        _print_failure(ReadOnlyAdapterError(ReadOnlyErrorCode.INVALID_LOCAL_INPUT))
        return 1

    print(run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
