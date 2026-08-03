from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from pydantic import ValidationError

from research_sources.projector import project_compatibility
from research_sources.source_graph import (
    ProjectionValidationReportV0,
    SourceProjectionBundleV0,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = Path(
    os.environ.get("B10_R04_REPO_ROOT", PROJECT_ROOT)
)
ARTIFACT = (
    REPO_ROOT
    / "corpus/research_sources/related-wikisource/source-projection-pilot-v0.json"
)
SCRIPT = PROJECT_ROOT / "scripts/build_b10_r04_source_projection.py"


def _builder_module():
    spec = importlib.util.spec_from_file_location("b10_r04_builder", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _artifact_bundle() -> SourceProjectionBundleV0:
    return SourceProjectionBundleV0.model_validate(
        json.loads(ARTIFACT.read_text("utf-8"))
    )


def test_committed_artifact_is_closed_typed_and_rebuildable() -> None:
    builder = _builder_module()
    committed = ARTIFACT.read_bytes()
    bundle = _artifact_bundle()
    rebuilt = builder.build_validated_bundle(REPO_ROOT)

    assert bundle.schema_version == "source-projection-bundle/pilot-v0"
    assert bundle.research_only is True
    assert bundle.source_object_count == 31
    assert bundle.evidence_link_count == 20
    assert len(bundle.nodes) == 76
    assert len(bundle.bibliographic_edges) == 69
    assert bundle.pilot_case_ids == ("C14", "C45", "C47")
    assert bundle.title_based_merges == ()
    assert bundle.accepted_independent_witness_assertions == ()
    assert bundle.deferred_independent_witness_assertion_count > 0
    assert bundle.validation_report is not None
    assert bundle.validation_report.status == "PASS"
    assert len(bundle.assertions) == 155
    assert bundle.validation_report.source_replay_actual == 31
    assert bundle.validation_report.reverse_mapping_actual == 20
    assert bundle.validation_report.orphan_graph_node_count == 0
    assert bundle.validation_report.orphan_graph_edge_count == 0
    assert bundle.validation_report.orphan_assertion_count == 0
    assert bundle.validation_report.orphan_evidence_link_count == 0
    assert bundle.validation_report.layer_a_before.file_count == 50
    assert bundle.validation_report.layer_a_before.total_byte_count == 1_168_547
    assert (
        bundle.validation_report.layer_a_before.sha256
        == "7126f5f18c027b94ecb1a0a173b14b642e4d14e075a524203e28a1c6b40dd3fa"
    )
    assert bundle.validation_report.layer_a_before == bundle.validation_report.layer_a_after
    assert bundle.validation_report.rule_identity_fixture_before == ()
    assert bundle.validation_report.rule_identity_fixture_after == ()
    assert all(
        value == "NOT_RUN"
        for value in bundle.validation_report.forbidden_side_effects.model_dump().values()
    )
    assert builder.artifact_file_bytes(rebuilt) == committed
    assert rebuilt.canonical_json_bytes() == bundle.canonical_json_bytes()


def test_artifact_reverse_projection_and_raw_identities_match_layer_a() -> None:
    bundle = _artifact_bundle()
    projection = project_compatibility(bundle)
    package = REPO_ROOT / "corpus/research_sources/related-wikisource"
    assert projection.manifest_document == json.loads(
        (package / "accession-manifest.json").read_text("utf-8")
    )
    assert projection.mapping_document == json.loads(
        (package / "core14-mapping.json").read_text("utf-8")
    )
    for source in bundle.source_objects:
        raw = REPO_ROOT / source.raw_path
        assert raw.stat().st_size == source.raw_byte_count
        import hashlib

        assert hashlib.sha256(raw.read_bytes()).hexdigest() == source.raw_sha256


def test_builder_check_is_read_only_and_rejects_unknown_flags() -> None:
    before = ARTIFACT.read_bytes()
    env = dict(os.environ)
    command = [
        os.environ.get("CODEX_PRIMARY_RUNTIME_PYTHON", "python3"),
        str(SCRIPT),
        "--repo-root",
        str(REPO_ROOT),
        "--check",
    ]
    completed = subprocess.run(command, env=env, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    assert ARTIFACT.read_bytes() == before

    rejected = subprocess.run(
        command + ["--unexpected"], env=env, capture_output=True, text=True
    )
    assert rejected.returncode != 0
    assert ARTIFACT.read_bytes() == before


def test_no_overwrite_publication_has_one_winner_and_preserves_existing(
    tmp_path: Path,
) -> None:
    builder = _builder_module()
    target = tmp_path / "pilot.json"
    target.write_bytes(b"existing")
    with pytest.raises(builder.BuildProjectionError, match="artifact-exists"):
        builder.write_artifact_no_overwrite(target, b"replacement")
    assert target.read_bytes() == b"existing"

    concurrent = tmp_path / "concurrent.json"

    def publish() -> str:
        try:
            builder.write_artifact_no_overwrite(concurrent, b"complete")
            return "published"
        except builder.BuildProjectionError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: publish(), range(2)))
    assert sorted(results) == ["artifact-exists", "published"]
    assert concurrent.read_bytes() == b"complete"
    assert not list(tmp_path.glob(".*.tmp-*"))


@pytest.mark.parametrize(
    ("mutation", "expected_case"),
    (
        ("remove-c14-m16", "C14"),
        ("inflate-c14-m07", "C14"),
        ("remove-c47-locators", "C47"),
    ),
)
def test_pilot_pass_requires_exact_case_denominators(
    mutation: str, expected_case: str
) -> None:
    builder = _builder_module()
    bundle = builder.build_validated_bundle(REPO_ROOT)
    links = list(bundle.evidence_links)
    if mutation == "remove-c14-m16":
        links = [link for link in links if link.mapping_id != "B10-R03-M16"]
    elif mutation == "inflate-c14-m07":
        links = [
            link.model_copy(update={"target_atom_ids": ("C14-R01",)})
            if link.mapping_id == "B10-R03-M07"
            else link
            for link in links
        ]
    else:
        links = [
            link
            for link in links
            if link.mapping_id not in {"B10-R03-M15", "B10-R03-M17"}
        ]
    damaged = bundle.model_copy(update={"evidence_links": tuple(links)})
    with pytest.raises(
        builder.BuildProjectionError, match=f"pilot-case-failed:{expected_case}"
    ):
        builder._pilot_case_checks(damaged)


def test_no_rule_fixture_status_rejects_invented_equal_digests() -> None:
    report = _artifact_bundle().validation_report
    assert report is not None
    payload = report.model_dump(mode="json")
    fake = {
        "path": "invented/rule-candidate.json",
        "sha256": "0" * 64,
    }
    payload["rule_identity_fixture_before"] = [fake]
    payload["rule_identity_fixture_after"] = [fake]
    with pytest.raises(ValidationError, match="empty fixture hash denominators"):
        ProjectionValidationReportV0.model_validate(payload)


def test_bundle_binds_report_deferred_witness_count() -> None:
    payload = _artifact_bundle().model_dump(mode="json")
    payload["validation_report"]["deferred_independent_witness_count"] += 1
    with pytest.raises(ValidationError, match="deferred-witness count is inconsistent"):
        SourceProjectionBundleV0.model_validate(payload)


def test_check_reader_rejects_artifact_symlink_even_with_identical_bytes(
    tmp_path: Path,
) -> None:
    builder = _builder_module()
    package = tmp_path / "corpus/research_sources/related-wikisource"
    package.mkdir(parents=True)
    external = tmp_path.parent / f"{tmp_path.name}-external.json"
    external.write_bytes(b"same")
    artifact = package / "source-projection-pilot-v0.json"
    artifact.symlink_to(external)
    with pytest.raises(builder.BuildProjectionError, match="artifact-symlink-forbidden"):
        builder._read_regular_artifact(tmp_path, artifact)


def test_publication_wraps_link_failure_and_cleans_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    builder = _builder_module()
    target = tmp_path / "pilot.json"

    def fail_link(*_args: object, **_kwargs: object) -> None:
        raise OSError("machine path must not leak")

    monkeypatch.setattr(builder.os, "link", fail_link)
    with pytest.raises(
        builder.BuildProjectionError, match="artifact-link-failed:OSError"
    ) as caught:
        builder.write_artifact_no_overwrite(target, b"complete")
    assert str(tmp_path) not in str(caught.value)
    assert not target.exists()
    assert not list(tmp_path.glob(".*.tmp-*"))


def test_post_link_fsync_failure_reports_published_complete_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    builder = _builder_module()
    target = tmp_path / "pilot.json"
    real_fsync = builder.os.fsync
    calls = 0

    def fail_directory_fsync(descriptor: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("machine path must not leak")
        real_fsync(descriptor)

    monkeypatch.setattr(builder.os, "fsync", fail_directory_fsync)
    with pytest.raises(
        builder.BuildProjectionError,
        match="artifact-published-durability-uncertain:OSError",
    ) as caught:
        builder.write_artifact_no_overwrite(target, b"complete")
    assert str(tmp_path) not in str(caught.value)
    assert target.read_bytes() == b"complete"
    assert not list(tmp_path.glob(".*.tmp-*"))


def test_post_link_cleanup_failure_never_leaks_raw_oserror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    builder = _builder_module()
    target = tmp_path / "pilot.json"

    def fail_unlink(*_args: object, **_kwargs: object) -> None:
        raise OSError("machine path must not leak")

    monkeypatch.setattr(builder.os, "unlink", fail_unlink)
    with pytest.raises(
        builder.BuildProjectionError,
        match="artifact-published-cleanup-uncertain:OSError",
    ) as caught:
        builder.write_artifact_no_overwrite(target, b"complete")
    assert str(tmp_path) not in str(caught.value)
    assert target.read_bytes() == b"complete"
