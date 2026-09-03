from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Mapping

import pytest

import scripts.run_video_feedback_loop_s1 as s1_cli
from src.connectors.evidence_resolver import EvidenceResolverContext, resolve_evidence
from src.video_pipeline.feedback_loop.contracts_v1 import FeedbackLoopRunV1
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalEvidenceQueryPlanV1,
    LocalKBSourceSnapshotV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
    SourceSnapshotBindingV1,
    bind_source_snapshot_to_plan,
)
from src.video_pipeline.feedback_loop.source_snapshot_v1 import LocalKBSourceAccessor
from src.video_pipeline.feedback_loop.strict_local_files import (
    load_external_audit_v1,
    load_query_plan_v1,
    load_source_snapshot_v1,
)
from src.video_pipeline.package import PackageManifestV1, verify_package_members


APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parents[1]
AUDIT_PATH = (
    APP_ROOT
    / "data"
    / "video_pipeline"
    / "external_media"
    / "祖山觀"
    / "audits"
    / "episode-22.bundle.json"
)
FIXTURE_ROOT = WORKSPACE_ROOT / "tests" / "fixtures" / "video-feedback-loop" / "v1"
QUERY_PLAN_PATH = FIXTURE_ROOT / "episode-22-query-plan.json"
SOURCE_ID = "media:douyin:zushan:collection-7664842437629921326:episode-22"
AUDIT_ID = "audit:douyin:zushan:episode-22"
WORK_ID = "7669807398794598565"
CLAIM_IDS = (
    "claim:douyin:zushan:episode-22:01",
    "claim:douyin:zushan:episode-22:02",
)
QUERIES = ("毕宿 烈风 古典原文 来源", "烈风 海上风暴 古典对应关系")
BOOK_ID = "kaiyuan_zhanjing"
HERMETIC_COLLECTION = "test_vfl_ephemeral_episode_22"
LIVE_COLLECTION = "local_kb_kaiyuan_v2"
CORPUS_VERSION = "20260902T000000Z"
PROVENANCE_SHA256 = "c" * 64
RELATIVE_PATH = "古籍/唐開元占經/分卷/KR3g0018_031.md"
SOURCE_LOCATOR = "KR3g0018_031"
PAGE_MARKER = "KR3g0018_WYG_031-17a"
RAW_TEXT = "石氏曰熒惑守心。"
RAW_HASH = "sha256:491ab466667efbd8746a1feafcbb25e0baae29d1e40e49f3b958c081737f074f"
NORMALIZED_HASH = (
    "sha256:267c1200d1f1830640b44eee66d177d06e5fd178639eff629e74cfb2ab987b46"
)
TEST_CONTEXT = EvidenceResolverContext(
    source_root_label="task5-snapshot",
    ingest_source_label="task5-recording",
)
PACKAGE_PATHS = {
    "external-audit-bundle.json",
    "local-evidence-probes.json",
    "feedback-observations.json",
    "improvement-candidates.json",
    "video-production-request.json",
    "manual-publication-handoff.json",
    "feedback-loop-run.json",
    "manifest.json",
}


def _canonical(value: object, *, newline: bool = False) -> bytes:
    suffix = "\n" if newline else ""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + suffix
    ).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(_canonical(value, newline=True))


def _tree_hash(files: list[dict[str, object]]) -> str:
    return hashlib.sha256(_canonical(files)).hexdigest()


def _plan_payload(*, live: bool = False) -> dict[str, object]:
    scope = "reviewed_live" if live else "hermetic_test"
    collection = LIVE_COLLECTION if live else HERMETIC_COLLECTION
    plan_id = (
        "query-plan:vfl:zushan:episode-22:reviewed-live-test-v1"
        if live
        else "query-plan:vfl:zushan:episode-22:v1"
    )
    return {
        "schema_version": "local-evidence-query-plan/v1",
        "plan_id": plan_id,
        "policy_version": "vfl-readonly-probe/1.0.0",
        "source_id": SOURCE_ID,
        "audit_id": AUDIT_ID,
        "execution_scope": scope,
        "collection": collection,
        "kb_book_id": BOOK_ID,
        "expected_corpus_version": CORPUS_VERSION,
        "requests": [
            {
                "request_id": f"query-request:vfl:zushan:episode-22:{index:02d}",
                "source_id": SOURCE_ID,
                "audit_id": AUDIT_ID,
                "claim_id": claim_id,
                "query": query,
                "kb_book_id": BOOK_ID,
                "query_mode": "evidence",
                "top_k": 8,
            }
            for index, (claim_id, query) in enumerate(
                zip(CLAIM_IDS, QUERIES, strict=True), start=1
            )
        ],
    }


def _write_source_snapshot(
    base: Path,
    *,
    live: bool = False,
) -> tuple[Path, Path, LocalKBSourceSnapshotV1]:
    root = base / "kb"
    source = root / RELATIVE_PATH
    source.parent.mkdir(parents=True)
    source.write_text(
        f"# 唐開元占經\n<pb:{PAGE_MARKER}>\n{RAW_TEXT}\n",
        encoding="utf-8",
    )
    raw = source.read_bytes()
    files: list[dict[str, object]] = [
        {
            "relative_path": RELATIVE_PATH,
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    ]
    payload = {
        "schema_version": "local-kb-source-snapshot/v1",
        "snapshot_id": "snapshot:vfl:zushan:episode-22:test-v1",
        "corpus_version": CORPUS_VERSION,
        "collection": LIVE_COLLECTION if live else HERMETIC_COLLECTION,
        "kb_book_id": BOOK_ID,
        "files": files,
        "tree_sha256": _tree_hash(files),
    }
    snapshot_path = base / "source-snapshot.json"
    _write_json(snapshot_path, payload)
    return root, snapshot_path, LocalKBSourceSnapshotV1.model_validate(payload)


def _stage_observability(
    *,
    stage: str,
    card_types: list[str],
    returned: int,
) -> dict[str, object]:
    return {
        "schema_version": "kb-observability/v1",
        "operation": "retrieve",
        "stage": stage,
        "latency_ms": 1.25,
        "upstream_latency_ms": 1.0,
        "requested_top_k": 8,
        "raw_pool_size": returned,
        "returned_pool_size": returned,
        "card_types": card_types,
        "collection": HERMETIC_COLLECTION,
        "corpus_version": CORPUS_VERSION,
        "upstream_provenance_sha256": PROVENANCE_SHA256,
        "corpus_provenance": "upstream_meta",
    }


def _recording_hit(*, added_secret: str | None = None) -> dict[str, object]:
    hit: dict[str, object] = {
        "chunk_id": "passage-31",
        "score": 0.98,
        "path": RELATIVE_PATH,
        "title": "KR3g0018_031.md",
        "snippet": added_secret or "retrieval snippet must not persist",
        "card_type": "fenjuan",
        "kb_book_id": BOOK_ID,
        "book_title": "唐開元占經",
        "evidence_level": "primary",
        "status": "official",
        "match_type": "exact_raw",
        "source_locator": SOURCE_LOCATOR,
        "page_marker": PAGE_MARKER,
        "heading_path": ["唐開元占經"],
        "paragraph_index": 0,
        "raw_start": 34,
        "raw_end": 42,
        "anchor_text": RAW_TEXT,
        "raw_content_hash": RAW_HASH,
        "normalized_content_hash": NORMALIZED_HASH,
    }
    if added_secret is not None:
        hit["untrusted_debug_path"] = f"/private/{added_secret}"
    return hit


def _recording_response(*, added_secret: str | None = None) -> dict[str, object]:
    hit = _recording_hit(added_secret=added_secret)
    structured_pool = ["zhusu_card", "term_card", "extract_card"]
    primary_pool = ["fenjuan", "fulltext"]
    stage1 = {
        "schema_version": "kb-retrieve/v2",
        "query_mode": "evidence",
        "retrieval_stage": "structured_recall",
        "card_types": structured_pool,
        "collection": HERMETIC_COLLECTION,
        "filters": {"kb_book_id": BOOK_ID},
        "hits": [],
        "exact_hits": [],
        "related_hits": [],
        "raw_hits": [],
        "inferred_hits": [],
        "retrieved_count": 0,
        "latency_ms": 1,
        "observability": _stage_observability(
            stage="structured_recall", card_types=structured_pool, returned=0
        ),
    }
    official = {
        "schema_version": "kb-retrieve/v2",
        "query_mode": "evidence",
        "retrieval_stage": "primary_evidence",
        "card_types": primary_pool,
        "collection": HERMETIC_COLLECTION,
        "filters": {"kb_book_id": BOOK_ID},
        "hits": [hit],
        "exact_hits": [hit],
        "related_hits": [],
        "raw_hits": [hit],
        "inferred_hits": [hit],
        "retrieved_count": 1,
        "latency_ms": 1,
        "observability": _stage_observability(
            stage="primary_evidence", card_types=primary_pool, returned=1
        ),
    }
    stage2 = {
        "schema_version": "kb-two-stage/v2",
        "source": "official_qdrant",
        "official_result": official,
        "raw_hits": [hit],
        "inferred_hits": [hit],
        "query_mode": "evidence",
        "retrieval_stage": "primary_evidence",
        "card_types": primary_pool,
        "normalized_query": "recording",
        "query_variants": ["recording"],
        "exact_hits": [hit],
        "related_hits": [],
        "hits": [hit],
        "primary_candidates": [hit],
        "candidate_overlay_hits": [],
        "structured_fallbacks": [],
        "official_primary_used": True,
        "official_primary_empty": False,
        "fallback_used": False,
        "fallback_reason": None,
        "files_scanned": 0,
        "matched_files": [],
        "matched_headings": [],
        "matched_quotes": [],
        "only_structured_no_primary": False,
    }
    stages = [
        {**stage1["observability"], "source": "official_qdrant"},
        {**official["observability"], "source": "official_qdrant"},
    ]
    return {
        "stage1": stage1,
        "stage2": stage2,
        "observability": {
            "schema_version": "kb-observability/v1",
            "operation": "two_stage_retrieve",
            "total_latency_ms": 3.0,
            "collection": HERMETIC_COLLECTION,
            "corpus_version": CORPUS_VERSION,
            "upstream_provenance_sha256": PROVENANCE_SHA256,
            "corpus_provenance": "upstream_meta",
            "provenance_conflicts": [],
            "fallback_reason": None,
            "stages": stages,
        },
    }


class RecordingTwoStageRetriever:
    """Concrete test-only retriever accepted by the hermetic binder."""

    def __init__(
        self,
        *,
        responses: list[object] | None = None,
        added_secret: str | None = None,
    ) -> None:
        self._binding: SourceSnapshotBindingV1 | None = None
        self._responses = responses or [
            _recording_response(added_secret=added_secret),
            _recording_response(added_secret=added_secret),
        ]
        self.calls: list[tuple[str, dict[str, object]]] = []

    @property
    def source_binding(self) -> SourceSnapshotBindingV1:
        assert self._binding is not None
        return self._binding

    def bind(self, binding: SourceSnapshotBindingV1) -> None:
        assert self._binding is None
        self._binding = binding

    def two_stage_retrieve(self, query: str, **kwargs: object) -> Mapping[str, object]:
        self.calls.append((query, dict(kwargs)))
        response = self._responses[len(self.calls) - 1]
        if isinstance(response, BaseException):
            raise response
        assert isinstance(response, Mapping)
        return deepcopy(response)


def _run_hermetic_s1(
    *,
    audit_path: Path,
    query_plan_path: Path,
    kb_root: Path,
    source_snapshot_path: Path,
    output: Path,
    retriever: RecordingTwoStageRetriever,
    resolver=resolve_evidence,
) -> str:
    assert type(retriever) is RecordingTwoStageRetriever
    audit_doc = load_external_audit_v1(audit_path)
    plan_doc = load_query_plan_v1(query_plan_path)
    snapshot_doc = load_source_snapshot_v1(source_snapshot_path)
    plan = plan_doc.value
    if (
        plan.execution_scope != "hermetic_test"
        or plan.collection != HERMETIC_COLLECTION
        or plan.source_id != audit_doc.value.source.source_id
        or plan.audit_id != audit_doc.value.audit.audit_id
        or tuple(request.claim_id for request in plan.requests) != CLAIM_IDS
    ):
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.PLAN_MISMATCH)
    bind_source_snapshot_to_plan(snapshot=snapshot_doc.value, plan=plan)
    with LocalKBSourceAccessor.open(
        kb_root=kb_root, snapshot=snapshot_doc.value
    ) as accessor:
        retriever.bind(accessor.binding)
        return s1_cli._complete_batch_build_publish(
            audit_doc=audit_doc,
            plan_doc=plan_doc,
            snapshot_doc=snapshot_doc,
            kb_root=kb_root,
            output=output,
            source_accessor=accessor,
            retriever=retriever,
            resolver_context=TEST_CONTEXT,
            resolver=resolver,
        )


def _package_members(output: Path) -> tuple[PackageManifestV1, dict[str, bytes]]:
    manifest = PackageManifestV1.model_validate(
        json.loads((output / "manifest.json").read_bytes())
    )
    members = {
        entry.path: (output / entry.path).read_bytes() for entry in manifest.members
    }
    assert verify_package_members(manifest, members) is True
    return manifest, members


def _member_hash_list_sha256(manifest: PackageManifestV1) -> str:
    payload = [
        {"path": member.path, "sha256": member.sha256}
        for member in sorted(manifest.members, key=lambda item: item.path)
    ]
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _whole_tree_sha256(root: Path) -> str:
    payload: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            payload.append({"path": relative, "type": "directory"})
        else:
            payload.append(
                {
                    "path": relative,
                    "type": "file",
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _assert_no_staging(output: Path) -> None:
    assert not list(output.parent.glob(f".{output.name}.*"))


def _main_args(
    *,
    plan: Path,
    root: Path,
    snapshot: Path,
    output: Path,
) -> list[str]:
    return [
        "--audit",
        str(AUDIT_PATH),
        "--query-plan",
        str(plan),
        "--kb-root",
        str(root),
        "--source-snapshot",
        str(snapshot),
        "--output",
        str(output),
    ]


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(WORKSPACE_ROOT / "packages" / "kb-contracts" / "python"),
            str(WORKSPACE_ROOT / "packages" / "kb-text-core" / "python"),
        ]
    )
    return env


def test_episode_22_two_fresh_builds_emit_safe_hash_evidence(tmp_path: Path) -> None:
    """Catches machine paths or input order entering canonical S1 package identity."""
    plan = load_query_plan_v1(QUERY_PLAN_PATH).value
    roots: list[Path] = []
    outputs: list[Path] = []
    run_ids: list[str] = []
    package_bytes: list[dict[str, bytes]] = []
    manifests: list[PackageManifestV1] = []
    for index in (1, 2):
        root, snapshot, _ = _write_source_snapshot(tmp_path / f"snapshot-{index}")
        output = tmp_path / f"output-{index}"
        retriever = RecordingTwoStageRetriever()
        run_id = _run_hermetic_s1(
            audit_path=AUDIT_PATH,
            query_plan_path=QUERY_PLAN_PATH,
            kb_root=root,
            source_snapshot_path=snapshot,
            output=output,
            retriever=retriever,
        )
        manifest, members = _package_members(output)
        roots.append(root)
        outputs.append(output)
        run_ids.append(run_id)
        manifests.append(manifest)
        package_bytes.append(members)
        assert retriever.calls == [
            (
                request.query,
                {
                    "top_k": 8,
                    "collection": HERMETIC_COLLECTION,
                    "filters": {"kb_book_id": BOOK_ID},
                    "query_mode": "evidence",
                },
            )
            for request in plan.requests
        ]
        assert set(path.name for path in output.iterdir()) == PACKAGE_PATHS
        _assert_no_staging(output)

    assert roots[0] != roots[1]
    assert run_ids[0] == run_ids[1]
    assert manifests[0] == manifests[1]
    assert package_bytes[0] == package_bytes[1]
    manifest_sha = hashlib.sha256(
        (outputs[0] / "manifest.json").read_bytes()
    ).hexdigest()
    member_list_sha = _member_hash_list_sha256(manifests[0])
    print(
        f"\nS1_E2E_HASH_EVIDENCE run_id={run_ids[0]} "
        f"manifest_sha256={manifest_sha} member_hash_list_sha256={member_list_sha}"
    )


def test_occupied_output_preserves_tree_and_leaves_no_staging(tmp_path: Path) -> None:
    """Catches no-replace publication mutating any member of an occupied tree."""
    root, snapshot, _ = _write_source_snapshot(tmp_path / "snapshot")
    output = tmp_path / "occupied"
    nested = output / "owned" / "directory"
    nested.mkdir(parents=True)
    (nested / "marker.txt").write_text("user-owned\n", encoding="utf-8")
    before = _whole_tree_sha256(output)

    with pytest.raises(FileExistsError):
        _run_hermetic_s1(
            audit_path=AUDIT_PATH,
            query_plan_path=QUERY_PLAN_PATH,
            kb_root=root,
            source_snapshot_path=snapshot,
            output=output,
            retriever=RecordingTwoStageRetriever(),
        )

    after = _whole_tree_sha256(output)
    staging = list(output.parent.glob(f".{output.name}.*"))
    staging_entries = len(staging)
    assert before == after
    assert staging_entries == 0
    print(
        "\nS1_OCCUPIED_OUTPUT_EVIDENCE "
        f"before_tree_sha256={before} after_tree_sha256={after} "
        f"staging_entries={staging_entries}"
    )


def test_second_request_failure_leaves_no_output_or_staging(tmp_path: Path) -> None:
    """Catches a completed first probe becoming a visible partial package."""
    root, snapshot, _ = _write_source_snapshot(tmp_path / "snapshot")
    output = tmp_path / "failed"
    retriever = RecordingTwoStageRetriever(
        responses=[
            _recording_response(),
            ReadOnlyAdapterError(ReadOnlyErrorCode.TRANSPORT_FAILED),
        ]
    )

    with pytest.raises(ReadOnlyAdapterError) as caught:
        _run_hermetic_s1(
            audit_path=AUDIT_PATH,
            query_plan_path=QUERY_PLAN_PATH,
            kb_root=root,
            source_snapshot_path=snapshot,
            output=output,
            retriever=retriever,
        )

    assert caught.value.code is ReadOnlyErrorCode.TRANSPORT_FAILED
    assert caught.value.failed_claim_id == CLAIM_IDS[1]
    output_exists = output.exists()
    staging_entries = len(list(output.parent.glob(f".{output.name}.*")))
    assert output_exists is False
    assert staging_entries == 0
    print(
        "\nS1_SECOND_REQUEST_FAILURE_EVIDENCE "
        f"output_exists={str(output_exists).lower()} "
        f"staging_entries={staging_entries}"
    )


def test_stdout_stderr_and_package_add_no_retrieval_secrets(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Catches retrieved text, body detail, credentials, or paths entering output."""
    retrieval_secret = "retrieval-body-sentinel-63bc"
    api_key = "".join(("test", "-api", "-credential"))
    root, snapshot, _ = _write_source_snapshot(tmp_path / "snapshot")
    output = tmp_path / "safe-output"
    seen_contexts: list[EvidenceResolverContext] = []

    def recording_resolver(
        evidence: Mapping[str, object],
        kb_root: Path,
        *,
        passage_loader: object,
        resolver_context: EvidenceResolverContext,
    ) -> Mapping[str, object]:
        seen_contexts.append(resolver_context)
        return resolve_evidence(
            evidence,
            kb_root,
            passage_loader=passage_loader,
            resolver_context=resolver_context,
        )

    monkeypatch.setenv("KB_SEARCH_API_KEY", api_key)
    _run_hermetic_s1(
        audit_path=AUDIT_PATH,
        query_plan_path=QUERY_PLAN_PATH,
        kb_root=root,
        source_snapshot_path=snapshot,
        output=output,
        retriever=RecordingTwoStageRetriever(added_secret=retrieval_secret),
        resolver=recording_resolver,
    )
    captured = capsys.readouterr()
    package_surfaces = {
        path.name: path.read_bytes() for path in output.iterdir() if path.is_file()
    }
    forbidden_fields = {
        "api_key": (api_key,),
        "raw_response_body": (f"/private/{retrieval_secret}",),
        "retrieved_text": (retrieval_secret, RAW_TEXT),
        "kb_root": (str(root),),
        "absolute_source_path": (str(root / RELATIVE_PATH),),
    }
    assert seen_contexts == [TEST_CONTEXT, TEST_CONTEXT]
    assert all(item is TEST_CONTEXT for item in seen_contexts)
    assert set(package_surfaces) == PACKAGE_PATHS

    sentinel = "INVALID-CORPUS-SECRET-7f42"
    bad_plan = tmp_path / "bad-plan.json"
    bad_payload = _plan_payload(live=True)
    bad_payload["expected_corpus_version"] = sentinel
    _write_json(bad_plan, bad_payload)
    live_root, live_snapshot, _ = _write_source_snapshot(tmp_path / "live", live=True)
    failed_output = tmp_path / "invalid-corpus-output"
    factory_calls = 0

    def forbidden_factory(*args: object, **kwargs: object) -> object:
        nonlocal factory_calls
        factory_calls += 1
        raise AssertionError("invalid corpus must fail before factory")

    monkeypatch.setattr(s1_cli, "build_readonly_kb_retriever", forbidden_factory)
    assert s1_cli.main(
        _main_args(
            plan=bad_plan,
            root=live_root,
            snapshot=live_snapshot,
            output=failed_output,
        )
    ) == 1
    rejected = capsys.readouterr()
    assert rejected.out == ""
    assert rejected.err == "invalid_local_input\n"
    assert sentinel not in rejected.err
    assert factory_calls == 0
    assert not failed_output.exists()
    _assert_no_staging(failed_output)
    assert all(sentinel not in path.name for path in tmp_path.iterdir())
    checked_surfaces = {
        "stdout": (captured.out.encode("utf-8"), rejected.out.encode("utf-8")),
        "stderr": (captured.err.encode("utf-8"), rejected.err.encode("utf-8")),
        "package": tuple(package_surfaces.values()),
    }
    privacy_checks = {
        field_name: {
            surface_name: all(
                sentinel_value.encode("utf-8") not in surface_bytes
                for sentinel_value in sentinels
                for surface_bytes in surface_values
            )
            for surface_name, surface_values in checked_surfaces.items()
        }
        for field_name, sentinels in forbidden_fields.items()
    }
    privacy_passed = all(
        surface_passed
        for field_checks in privacy_checks.values()
        for surface_passed in field_checks.values()
    )
    privacy_status = "PASS" if privacy_passed else "FAIL"
    assert privacy_status == "PASS"
    print(
        "\nS1_PRIVACY_EVIDENCE "
        f"fields={','.join(privacy_checks)} "
        f"surfaces={','.join(checked_surfaces)} status={privacy_status}"
    )


def test_public_main_has_no_retriever_injection_and_help_is_bounded(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Catches a public test bypass or an unsafe option entering the CLI surface."""
    assert tuple(inspect.signature(s1_cli.main).parameters) == ("argv",)
    with pytest.raises(SystemExit) as caught:
        s1_cli.main(["--help"])
    assert caught.value.code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    option_names = set(re.findall(r"--[a-z][a-z-]*", captured.out))
    assert option_names == {
        "--audit",
        "--query-plan",
        "--kb-root",
        "--source-snapshot",
        "--output",
    }
    assert all(
        token not in captured.out
        for token in ("--api-key", "--base-url", "--collection", "--corpus", "--probes", "--outcome")
    )


@pytest.mark.parametrize(
    "argv",
    [
        ["--api-key", "argv-secret-42"],
        ["--audit"],
        ["unexpected-positional"],
        ["--query", "private-abbreviation-secret"],
        ["--source", "private-abbreviation-secret"],
        ["-h", "short-help-sentinel"],
    ],
)
def test_parser_failures_emit_only_the_fixed_code_without_argv(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Catches argparse usage/error output reflecting hostile argv bytes."""
    assert s1_cli.main(argv) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "invalid_local_input\n"
    assert all(value not in captured.err for value in argv)


@pytest.mark.parametrize(
    ("failed_claim_id", "expected"),
    [
        (CLAIM_IDS[1], f"transport_failed claim_id={CLAIM_IDS[1]}\n"),
        ("INVALID-CLAIM-secret-42", "transport_failed\n"),
    ],
)
def test_failure_output_allows_only_code_and_a_validated_claim_id(
    failed_claim_id: str,
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Catches an unvalidated failure detail entering the safe CLI channel."""
    s1_cli._print_failure(
        ReadOnlyAdapterError(
            ReadOnlyErrorCode.TRANSPORT_FAILED,
            failed_claim_id=failed_claim_id,
        )
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == expected


def test_public_main_rejects_committed_hermetic_plan_before_factory(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Catches the committed recording plan reaching credentials or network."""
    root, snapshot, _ = _write_source_snapshot(tmp_path / "snapshot")
    output = tmp_path / "forbidden"
    calls = 0

    def forbidden_factory(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("hermetic plan reached production factory")

    monkeypatch.setattr(s1_cli, "build_readonly_kb_retriever", forbidden_factory)
    assert s1_cli.main(
        _main_args(
            plan=QUERY_PLAN_PATH,
            root=root,
            snapshot=snapshot,
            output=output,
        )
    ) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "plan_mismatch\n"
    assert calls == 0
    assert not output.exists()
    _assert_no_staging(output)


@pytest.mark.parametrize("mutation", ["work", "book", "request_book"])
def test_public_pilot_identity_gate_precedes_factory(
    mutation: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Catches a non-episode-22 work or non-pilot book reaching credentials."""
    plan_payload = _plan_payload(live=True)
    audit_payload = json.loads(AUDIT_PATH.read_bytes())
    if mutation == "work":
        audit_payload["source"]["platform_work_id"] = "7669807398794598566"
    elif mutation == "book":
        plan_payload["kb_book_id"] = "other_book"
        for request in plan_payload["requests"]:
            request["kb_book_id"] = "other_book"
    else:
        plan_payload["requests"][0]["kb_book_id"] = "other_book"
    plan_path = tmp_path / "plan.json"
    audit_path = tmp_path / "audit.json"
    _write_json(plan_path, plan_payload)
    _write_json(audit_path, audit_payload)
    root, snapshot_path, snapshot = _write_source_snapshot(tmp_path / "snapshot", live=True)
    if mutation == "book":
        snapshot_payload = snapshot.model_dump(mode="json")
        snapshot_payload["kb_book_id"] = "other_book"
        _write_json(snapshot_path, snapshot_payload)
    output = tmp_path / "output"
    calls = 0

    def forbidden_factory(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("pilot identity mismatch reached factory")

    monkeypatch.setattr(s1_cli, "build_readonly_kb_retriever", forbidden_factory)
    args = _main_args(plan=plan_path, root=root, snapshot=snapshot_path, output=output)
    args[1] = str(audit_path)
    assert s1_cli.main(args) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err in {"invalid_local_input\n", "plan_mismatch\n"}
    assert calls == 0
    assert not output.exists()


@pytest.mark.parametrize(
    "present",
    [
        (),
        ("VFL_S1_AUDIT",),
        ("VFL_S1_AUDIT", "VFL_S1_QUERY_PLAN"),
        ("VFL_S1_AUDIT", "VFL_S1_QUERY_PLAN", "VFL_S1_KB_ROOT"),
        (
            "VFL_S1_AUDIT",
            "VFL_S1_QUERY_PLAN",
            "VFL_S1_KB_ROOT",
            "VFL_S1_SOURCE_SNAPSHOT",
        ),
    ],
)
def test_make_target_requires_all_five_public_values(present: tuple[str, ...]) -> None:
    """Catches a Make target choosing any hidden path default."""
    values = {
        "VFL_S1_AUDIT": "audit",
        "VFL_S1_QUERY_PLAN": "plan",
        "VFL_S1_KB_ROOT": "root",
        "VFL_S1_SOURCE_SNAPSHOT": "snapshot",
        "VFL_S1_OUTPUT": "output",
    }
    result = subprocess.run(
        [
            "make",
            "-s",
            "vfl-s1-run",
            f"PYTHON={sys.executable}",
            *(f"{name}={values[name]}" for name in present),
        ],
        cwd=WORKSPACE_ROOT,
        env=_subprocess_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    missing = next(name for name in values if name not in present)
    assert result.returncode != 0
    assert result.stdout == ""
    error_lines = result.stderr.splitlines()
    assert error_lines[0] == f"{missing} is required"
    assert len(error_lines) == 2
    assert error_lines[1].startswith("make: *** [Makefile:")


def _write_argv_shim(path: Path, capture: Path) -> None:
    path.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        f"open({str(capture)!r}, 'w', encoding='utf-8').write("
        "json.dumps({'argv': sys.argv[1:], 'environment': {k: v for k, v in os.environ.items() if k.startswith('VFL_S1_')}}, ensure_ascii=False))\n",
        encoding="utf-8",
    )
    path.chmod(0o700)


def test_make_target_preserves_literal_paths_and_private_aliases(tmp_path: Path) -> None:
    """Catches Make/shell evaluation or command-line replacement of private aliases."""
    capture = tmp_path / "argv.json"
    shim = tmp_path / "python-shim"
    _write_argv_shim(shim, capture)
    make_expression = "$(shell printf MAKE_FUNCTION_EXECUTED >&2)"
    shell_expression = "$(printf SHELL_FUNCTION_EXECUTED >&2)"
    values = {
        "VFL_S1_AUDIT": f"audit space ' quote \" backtick` dollar$ {make_expression}",
        "VFL_S1_QUERY_PLAN": f"plan-{shell_expression}",
        "VFL_S1_KB_ROOT": "root with spaces/$literal/`literal`",
        "VFL_S1_SOURCE_SNAPSHOT": "snapshot-'single'-\"double\"",
        "VFL_S1_OUTPUT": "output-$()-`not-run`",
    }
    private = {
        "VFL_S1_AUDIT_PATH": "hostile-audit",
        "VFL_S1_QUERY_PLAN_PATH": "hostile-plan",
        "VFL_S1_KB_ROOT_PATH": "hostile-root",
        "VFL_S1_SOURCE_SNAPSHOT_PATH": "hostile-snapshot",
        "VFL_S1_OUTPUT_PATH": "hostile-output",
    }
    result = subprocess.run(
        [
            "make",
            "-s",
            "vfl-s1-run",
            f"PYTHON={shim}",
            *(f"{name}={value}" for name, value in values.items()),
            *(f"{name}={value}" for name, value in private.items()),
        ],
        cwd=WORKSPACE_ROOT,
        env=_subprocess_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert "MAKE_FUNCTION_EXECUTED" not in result.stderr
    assert "SHELL_FUNCTION_EXECUTED" not in result.stderr
    recorded = json.loads(capture.read_bytes())
    assert recorded["argv"] == [
        "apps/star-omen/scripts/run_video_feedback_loop_s1.py",
        "--audit",
        values["VFL_S1_AUDIT"],
        "--query-plan",
        values["VFL_S1_QUERY_PLAN"],
        "--kb-root",
        values["VFL_S1_KB_ROOT"],
        "--source-snapshot",
        values["VFL_S1_SOURCE_SNAPSHOT"],
        "--output",
        values["VFL_S1_OUTPUT"],
    ]
    assert recorded["environment"] == {
        private_name: values[public_name]
        for private_name, public_name in (
            ("VFL_S1_AUDIT_PATH", "VFL_S1_AUDIT"),
            ("VFL_S1_QUERY_PLAN_PATH", "VFL_S1_QUERY_PLAN"),
            ("VFL_S1_KB_ROOT_PATH", "VFL_S1_KB_ROOT"),
            ("VFL_S1_SOURCE_SNAPSHOT_PATH", "VFL_S1_SOURCE_SNAPSHOT"),
            ("VFL_S1_OUTPUT_PATH", "VFL_S1_OUTPUT"),
        )
    }


class _ProductionStub:
    def __init__(self, *, secret: str) -> None:
        self.secret = secret
        self.calls: list[dict[str, object]] = []
        self.violations: list[str] = []
        self.meta = {
            "meta_status": "ok",
            "schema_version": "corpus-manifest/v1",
            "corpus_version": CORPUS_VERSION,
            "ingest_run_id": "ingest_20260902T000000Z",
            "source_manifest_hash": "sha256:" + "a" * 64,
            "collection": LIVE_COLLECTION,
            "created_at": "2026-09-02T00:00:00Z",
            "managed_by": "local-kb-unified/v2",
            "collection_schema": "passage-v2",
            "run_stats": {
                "desired": 1,
                "new": 0,
                "changed": 0,
                "unchanged": 1,
                "stale": 0,
                "upserted": 0,
                "deleted": 0,
                "errors": 0,
                "elapsed_ms": 1,
            },
        }
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format: str, *args: object) -> None:
                return

            def _reply(self, status: int, value: object) -> None:
                raw = _canonical(value)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self) -> None:  # noqa: N802
                owner.calls.append({"method": "GET", "path": self.path})
                if self.path != "/v1/meta":
                    owner.violations.append("unexpected GET")
                    self._reply(404, {})
                    return
                if self.headers.get("Authorization") or self.headers.get("X-API-Key"):
                    owner.violations.append("meta carried credential")
                self._reply(200, owner.meta)

            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                try:
                    payload = json.loads(self.rfile.read(length))
                except Exception:
                    owner.violations.append("invalid request JSON")
                    self._reply(400, {})
                    return
                owner.calls.append(
                    {"method": "POST", "path": self.path, "payload": payload}
                )
                if self.path != "/v1/retrieve":
                    owner.violations.append("unexpected POST")
                if self.headers.get("Authorization") != f"Bearer {owner.secret}":
                    owner.violations.append("wrong authorization")
                if self.headers.get("X-API-Key") != owner.secret:
                    owner.violations.append("wrong api key")
                expected_keys = {
                    "schema_version",
                    "query",
                    "top_k",
                    "collection",
                    "query_mode",
                    "retrieval_stage",
                    "literal_first",
                    "card_types",
                    "filters",
                }
                if set(payload) != expected_keys:
                    owner.violations.append("wrong payload fields")
                stage = payload.get("retrieval_stage")
                expected_pool = (
                    ["zhusu_card", "term_card", "extract_card"]
                    if stage == "structured_recall"
                    else ["fenjuan", "fulltext"]
                )
                if (
                    payload.get("schema_version") != "kb-retrieve/v2"
                    or payload.get("query") not in QUERIES
                    or payload.get("top_k") != 8
                    or payload.get("collection") != LIVE_COLLECTION
                    or payload.get("query_mode") != "evidence"
                    or payload.get("literal_first") is not True
                    or payload.get("card_types") != expected_pool
                    or payload.get("filters") != {"kb_book_id": BOOK_ID}
                ):
                    owner.violations.append("wrong payload value")
                hits: list[dict[str, object]] = []
                if stage == "primary_evidence":
                    hits = [
                        {
                            "chunk_id": "passage-31",
                            "score": 0.98,
                            "path": RELATIVE_PATH,
                            "title": "KR3g0018_031.md",
                            "snippet": str(payload.get("query")),
                            "card_type": "fenjuan",
                            "kb_book_id": BOOK_ID,
                            "book_title": "唐開元占經",
                            "evidence_level": "primary",
                            "status": "official",
                            "source_locator": SOURCE_LOCATOR,
                            "page_marker": PAGE_MARKER,
                            "heading_path": ["唐開元占經"],
                            "paragraph_index": 0,
                            "raw_start": 34,
                            "raw_end": 42,
                            "raw_content_hash": RAW_HASH,
                            "normalized_content_hash": NORMALIZED_HASH,
                        }
                    ]
                self._reply(
                    200,
                    {
                        "schema_version": "kb-retrieve/v2",
                        "query_mode": "evidence",
                        "retrieval_stage": stage,
                        "card_types": expected_pool,
                        "collection": LIVE_COLLECTION,
                        "filters": {"kb_book_id": BOOK_ID},
                        "hits": hits,
                        "retrieved_count": len(hits),
                        "latency_ms": 1,
                    },
                )

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)

    @property
    def origin(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def __enter__(self) -> _ProductionStub:
        self.thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        assert not self.thread.is_alive()


def _write_live_inputs(base: Path) -> tuple[Path, Path, Path]:
    root, snapshot, _ = _write_source_snapshot(base / "snapshot", live=True)
    plan = base / "reviewed-plan.json"
    _write_json(plan, _plan_payload(live=True))
    return plan, root, snapshot


def _expected_retrieve_call(
    *,
    query: str,
    stage: str,
    card_types: list[str],
) -> dict[str, object]:
    return {
        "method": "POST",
        "path": "/v1/retrieve",
        "payload": {
            "schema_version": "kb-retrieve/v2",
            "query": query,
            "top_k": 8,
            "collection": LIVE_COLLECTION,
            "query_mode": "evidence",
            "retrieval_stage": stage,
            "literal_first": True,
            "card_types": card_types,
            "filters": {"kb_book_id": BOOK_ID},
        },
    }


def _expected_one_production_run_calls() -> list[dict[str, object]]:
    meta = {"method": "GET", "path": "/v1/meta"}
    structured = ["zhusu_card", "term_card", "extract_card"]
    primary = ["fenjuan", "fulltext"]
    return [
        meta,
        meta,
        meta,
        _expected_retrieve_call(
            query="毕宿 烈风 古典原文 来源",
            stage="structured_recall",
            card_types=structured,
        ),
        meta,
        meta,
        _expected_retrieve_call(
            query="毕宿 烈风 古典原文 来源",
            stage="primary_evidence",
            card_types=primary,
        ),
        meta,
        meta,
        meta,
        meta,
        _expected_retrieve_call(
            query="烈风 海上风暴 古典对应关系",
            stage="structured_recall",
            card_types=structured,
        ),
        meta,
        meta,
        _expected_retrieve_call(
            query="烈风 海上风暴 古典对应关系",
            stage="primary_evidence",
            card_types=primary,
        ),
        meta,
        meta,
    ]


def test_public_reviewed_live_make_uses_real_factory_and_loopback_stub(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Catches production assembly bypasses and CWD-relative config resolution."""
    secret = "".join(("loop", "back", "-credential"))
    plan, root, snapshot = _write_live_inputs(tmp_path)
    make_output = tmp_path / "make-output"
    main_output = tmp_path / "main-output"
    unrelated = tmp_path / "unrelated-cwd"
    unrelated.mkdir()

    with _ProductionStub(secret=secret) as stub:
        env = _subprocess_env()
        env["KB_SEARCH_BASE_URL"] = stub.origin
        env["KB_SEARCH_API_KEY"] = secret
        env.pop("APP_CONFIG_PATH", None)
        make_result = subprocess.run(
            [
                "make",
                "-s",
                "vfl-s1-run",
                f"PYTHON={sys.executable}",
                f"VFL_S1_AUDIT={AUDIT_PATH}",
                f"VFL_S1_QUERY_PLAN={plan}",
                f"VFL_S1_KB_ROOT={root}",
                f"VFL_S1_SOURCE_SNAPSHOT={snapshot}",
                f"VFL_S1_OUTPUT={make_output}",
            ],
            cwd=WORKSPACE_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert make_result.returncode == 0, make_result.stderr
        assert make_result.stderr == ""
        make_run_id = make_result.stdout.strip()
        assert re.fullmatch(r"feedback-run:vfl:[0-9a-f]{64}", make_run_id)

        monkeypatch.setenv("KB_SEARCH_BASE_URL", stub.origin)
        monkeypatch.setenv("KB_SEARCH_API_KEY", secret)
        monkeypatch.delenv("APP_CONFIG_PATH", raising=False)
        monkeypatch.chdir(unrelated)
        assert s1_cli.main(
            _main_args(
                plan=plan,
                root=root,
                snapshot=snapshot,
                output=main_output,
            )
        ) == 0
        main_captured = capsys.readouterr()

    assert main_captured.err == ""
    assert main_captured.out.strip() == make_run_id
    assert stub.violations == []
    expected_run_calls = _expected_one_production_run_calls()
    assert stub.calls == [*expected_run_calls, *expected_run_calls]
    make_manifest, make_members = _package_members(make_output)
    main_manifest, main_members = _package_members(main_output)
    assert make_manifest == main_manifest
    assert make_members == main_members
    run = FeedbackLoopRunV1.model_validate(
        json.loads((make_output / "feedback-loop-run.json").read_bytes())
    )
    assert run.run_id == make_run_id
    assert all(probe.result_state == "unresolved" for probe in run.local_probes)
    assert [len(probe.evidence_references) for probe in run.local_probes] == [1, 1]
    assert all(
        reference.relationship == "context_only"
        for probe in run.local_probes
        for reference in probe.evidence_references
    )
    assert secret.encode() not in b"".join(make_members.values())
    _assert_no_staging(make_output)
    _assert_no_staging(main_output)
