from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from research_sources.core14_index import load_core14_target_index
from research_sources.projector import project_compatibility, project_source_bundle
from research_sources.source_graph import (
    build_pilot_case_checks,
    FileDigestV0,
    PilotCaseCheckV0,
    ProjectionValidationReportV0,
    SnapshotDigestV0,
    SourceProjectionBundleV0,
)
from research_sources.source_inventory import load_source_inventory


PACKAGE_RELATIVE = Path("corpus/research_sources/related-wikisource")
MANIFEST_RELATIVE = PACKAGE_RELATIVE / "accession-manifest.json"
MAPPING_RELATIVE = PACKAGE_RELATIVE / "core14-mapping.json"
ARTIFACT_RELATIVE = PACKAGE_RELATIVE / "source-projection-pilot-v0.json"
NO_RULE_FIXTURE_STATUS = "NO_VERSIONED_RULE_FIXTURE_IN_STABLE_BASELINE"


class BuildProjectionError(ValueError):
    """Fail-closed, path-safe error from the hermetic pilot builder."""


def _json_document(raw: bytes, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BuildProjectionError(f"invalid-json:{label}:{type(exc).__name__}") from None
    if not isinstance(value, Mapping):
        raise BuildProjectionError(f"invalid-json-shape:{label}")
    return value


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _layer_a_snapshot(repo_root: Path) -> SnapshotDigestV0:
    package = repo_root / PACKAGE_RELATIVE
    if not package.is_dir() or package.is_symlink():
        raise BuildProjectionError("invalid-layer-a-package")
    records: list[dict[str, Any]] = []
    total_bytes = 0
    for path in sorted(package.rglob("*")):
        if path == repo_root / ARTIFACT_RELATIVE:
            continue
        if path.is_symlink():
            raise BuildProjectionError("layer-a-symlink-forbidden")
        if not path.is_file():
            continue
        raw = path.read_bytes()
        total_bytes += len(raw)
        records.append(
            {
                "path": path.relative_to(repo_root).as_posix(),
                "sha256": _sha256(raw),
                "byte_count": len(raw),
            }
        )
    payload = json.dumps(
        records,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return SnapshotDigestV0(
        file_count=len(records),
        total_byte_count=total_bytes,
        sha256=_sha256(payload),
    )


def _pilot_case_checks(bundle: SourceProjectionBundleV0) -> tuple[PilotCaseCheckV0, ...]:
    try:
        return build_pilot_case_checks(
            bundle.evidence_links,
            bundle.source_objects,
            bundle.assertions,
        )
    except ValueError as exc:
        case = next(
            (case_id for case_id in ("C14", "C45", "C47") if case_id in str(exc)),
            "unknown",
        )
        raise BuildProjectionError(f"pilot-case-failed:{case}") from None


def _read_regular_artifact(repo_root: Path, artifact: Path) -> bytes:
    """Read an in-repository regular file without following any symlink component."""

    try:
        root = Path(repo_root).resolve(strict=True)
        target = Path(os.path.abspath(artifact))
        relative = target.relative_to(root)
        current = root
        for component in relative.parts:
            current = current / component
            if stat.S_ISLNK(os.lstat(current).st_mode):
                raise BuildProjectionError("artifact-symlink-forbidden")
        descriptor = os.open(target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise BuildProjectionError("artifact-not-regular")
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                return handle.read()
        finally:
            if descriptor >= 0:
                os.close(descriptor)
    except BuildProjectionError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise BuildProjectionError(
            f"artifact-unreadable:{type(exc).__name__}"
        ) from None


def build_validated_bundle(repo_root: Path) -> SourceProjectionBundleV0:
    """Build the research-only artifact in memory without network or source writes."""

    try:
        root = Path(repo_root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise BuildProjectionError(f"invalid-repo-root:{type(exc).__name__}") from None

    before = _layer_a_snapshot(root)
    manifest_raw = (root / MANIFEST_RELATIVE).read_bytes()
    mapping_raw = (root / MAPPING_RELATIVE).read_bytes()
    manifest = _json_document(manifest_raw, "source-manifest")
    mapping = _json_document(mapping_raw, "source-mapping")
    inventory = load_source_inventory(root)
    core14_index = load_core14_target_index(root)
    bundle = project_source_bundle(
        inventory,
        manifest,
        mapping,
        source_manifest_sha=_sha256(manifest_raw),
        source_mapping_sha=_sha256(mapping_raw),
        core14_index=core14_index,
    )
    reverse = project_compatibility(bundle)
    if reverse.manifest_document != manifest or reverse.mapping_document != mapping:
        raise BuildProjectionError("reverse-projection-mismatch")

    node_ids = {node.node_id for node in bundle.nodes}
    endpoint_ids = {
        endpoint
        for edge in bundle.bibliographic_edges
        for endpoint in (edge.source_node_id, edge.target_node_id)
    }
    orphan_nodes = len(node_ids - endpoint_ids)
    orphan_edges = sum(
        edge.source_node_id not in node_ids or edge.target_node_id not in node_ids
        for edge in bundle.bibliographic_edges
    )
    orphan_assertions = sum(
        assertion.subject_node_id not in node_ids for assertion in bundle.assertions
    )
    source_node_ids = {
        node.node_id for node in bundle.nodes if node.kind.value == "source_object"
    }
    orphan_links = sum(
        link.source_object_id not in source_node_ids
        or not core14_index.contains_case(link.target_case_id)
        or any(
            not core14_index.contains_atom(link.target_case_id, atom_id)
            for atom_id in link.target_atom_ids
        )
        for link in bundle.evidence_links
    )
    after = _layer_a_snapshot(root)
    audit_digests = tuple(
        FileDigestV0(path=item.path, sha256=item.sha256)
        for item in core14_index.audits
    )
    report = ProjectionValidationReportV0(
        schema_version="projection-validation-report/pilot-v0",
        status="PASS",
        source_manifest_sha256=bundle.source_manifest_sha,
        source_mapping_sha256=bundle.source_mapping_sha,
        source_replay_expected=int(manifest["accession_count"]),
        source_replay_actual=len(inventory.accessions),
        reverse_accession_expected=int(manifest["accession_count"]),
        reverse_accession_actual=len(reverse.manifest_document["accessions"]),
        reverse_mapping_expected=len(mapping["mappings"]),
        reverse_mapping_actual=len(reverse.mapping_document["mappings"]),
        graph_node_count=len(bundle.nodes),
        bibliographic_edge_count=len(bundle.bibliographic_edges),
        evidence_link_count=len(bundle.evidence_links),
        orphan_graph_node_count=orphan_nodes,
        orphan_graph_edge_count=orphan_edges,
        orphan_assertion_count=orphan_assertions,
        orphan_evidence_link_count=orphan_links,
        title_based_merge_count=len(bundle.title_based_merges),
        accepted_independent_witness_count=len(
            bundle.accepted_independent_witness_assertions
        ),
        deferred_independent_witness_count=(
            bundle.deferred_independent_witness_assertion_count
        ),
        pilot_cases=_pilot_case_checks(bundle),
        core14_manifest_sha256=core14_index.manifest_sha256,
        core14_audit_digests=audit_digests,
        layer_a_before=before,
        layer_a_after=after,
        rule_identity_fixture_status=NO_RULE_FIXTURE_STATUS,
        rule_identity_fixture_before=(),
        rule_identity_fixture_after=(),
        forbidden_side_effects=bundle.source_package_metadata.forbidden_side_effects,
    )
    payload = bundle.model_dump(mode="json", exclude_none=False)
    payload["validation_report"] = report.model_dump(mode="json")
    return SourceProjectionBundleV0.model_validate(payload)


def artifact_file_bytes(bundle: SourceProjectionBundleV0) -> bytes:
    if bundle.validation_report is None:
        raise BuildProjectionError("validation-report-required")
    return (
        json.dumps(
            bundle.model_dump(mode="json", exclude_none=False),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def write_artifact_no_overwrite(destination: Path, content: bytes) -> None:
    """Publish one sibling artifact atomically without replacing any target."""

    target = Path(destination)
    try:
        if os.path.lexists(target):
            raise BuildProjectionError("artifact-exists")
        if not target.parent.is_dir() or target.parent.is_symlink():
            raise BuildProjectionError("invalid-artifact-parent")
    except BuildProjectionError:
        raise
    except OSError as exc:
        raise BuildProjectionError(
            f"artifact-parent-unreadable:{type(exc).__name__}"
        ) from None
    temporary: Path | None = None
    try:
        try:
            with tempfile.NamedTemporaryFile(
                mode="xb",
                prefix=f".{target.name}.tmp-",
                dir=target.parent,
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise BuildProjectionError(
                f"artifact-publish-failed:{type(exc).__name__}"
            ) from None
        try:
            os.link(temporary, target)
        except FileExistsError:
            raise BuildProjectionError("artifact-exists") from None
        except OSError as exc:
            raise BuildProjectionError(
                f"artifact-link-failed:{type(exc).__name__}"
            ) from None
        try:
            os.unlink(temporary)
            temporary = None
        except OSError as exc:
            raise BuildProjectionError(
                f"artifact-published-cleanup-uncertain:{type(exc).__name__}"
            ) from None
        try:
            directory_fd = os.open(
                target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            )
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError as exc:
            raise BuildProjectionError(
                f"artifact-published-durability-uncertain:{type(exc).__name__}"
            ) from None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            except OSError:
                # The primary path-safe error already records whether publication
                # happened; cleanup failure must never replace it with a raw path.
                pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or verify the hermetic B10-R04 source projection pilot."
    )
    parser.add_argument("--repo-root", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write-new", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    bundle = build_validated_bundle(args.repo_root)
    expected = artifact_file_bytes(bundle)
    artifact = args.repo_root.resolve() / ARTIFACT_RELATIVE
    if args.check:
        actual = _read_regular_artifact(args.repo_root, artifact)
        if actual != expected:
            raise BuildProjectionError("artifact-byte-mismatch")
    else:
        write_artifact_no_overwrite(artifact, expected)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildProjectionError as exc:
        raise SystemExit(f"b10-r04-builder:{exc}") from None
