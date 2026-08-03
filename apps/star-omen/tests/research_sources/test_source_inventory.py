from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable

import pytest

from research_sources import SourceInventoryError, load_source_inventory


PACKAGE_RELATIVE = Path("corpus/research_sources/related-wikisource")


@pytest.fixture(scope="session")
def repo_root() -> Path:
    configured = os.environ.get("B10_R03_REPO_ROOT")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[4]


@pytest.fixture(scope="session")
def package_root(repo_root: Path) -> Path:
    return repo_root / PACKAGE_RELATIVE


@pytest.fixture
def mutable_repo(tmp_path: Path, repo_root: Path) -> Path:
    target = tmp_path / "repo"
    shutil.copytree(repo_root / "corpus", target / "corpus", symlinks=True)
    return target


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _manifest(repo: Path) -> dict[str, Any]:
    return _load_json(repo / PACKAGE_RELATIVE / "accession-manifest.json")


def _save_manifest(repo: Path, manifest: dict[str, Any]) -> None:
    _write_json(repo / PACKAGE_RELATIVE / "accession-manifest.json", manifest)


def _family_file(repo: Path, family: dict[str, Any]) -> Path:
    return repo / Path(family["accession_metadata_path"])


def _family_for(manifest: dict[str, Any], family_id: str) -> dict[str, Any]:
    return next(item for item in manifest["families"] if item["family_id"] == family_id)


def _detail_for(
    repo: Path, manifest: dict[str, Any], accession_id: str
) -> tuple[dict[str, Any], Path, list[dict[str, Any]], dict[str, Any]]:
    compact = next(
        item for item in manifest["accessions"] if item["accession_id"] == accession_id
    )
    family = _family_for(manifest, compact["family_id"])
    path = _family_file(repo, family)
    details = _load_json(path)
    detail = next(item for item in details if item["accession_id"] == accession_id)
    return family, path, details, detail


def _hash_package_files(package_root: Path) -> dict[str, str]:
    return {
        path.relative_to(package_root).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(package_root.rglob("*"))
        if path.is_file()
    }


def _assert_error(
    repo: Path,
    code: str,
    mutation: Callable[[Path], None],
) -> SourceInventoryError:
    mutation(repo)
    with pytest.raises(SourceInventoryError) as caught:
        load_source_inventory(repo)
    assert caught.value.code == code
    assert str(repo) not in str(caught.value)
    return caught.value


def test_inventory_joins_real_compact_and_detailed_records(repo_root: Path) -> None:
    inventory = load_source_inventory(repo_root)

    assert len(inventory.accessions) == 16
    assert inventory.family_count == 7
    assert inventory.raw_file_count == 16
    assert inventory.total_raw_byte_count == 645_044
    assert inventory.accession_ids == tuple(sorted(inventory.accession_ids))
    assert inventory.get("zhws-yisizhan-5-r854562").family_id == "yisizhan"
    assert inventory.get("zhws-yisizhan-5-r854562").core14_cases == (
        "C09",
        "C13",
    )
    assert inventory.get("zhws-houhanshu-100-r1753568").oldid == 1_753_568


def test_inventory_output_is_deterministic_under_input_reordering(
    mutable_repo: Path,
) -> None:
    baseline = load_source_inventory(mutable_repo).accession_ids
    manifest = _manifest(mutable_repo)
    manifest["families"].reverse()
    manifest["accessions"].reverse()
    _save_manifest(mutable_repo, manifest)
    for family in manifest["families"]:
        path = _family_file(mutable_repo, family)
        details = _load_json(path)
        details.reverse()
        _write_json(path, details)

    assert load_source_inventory(mutable_repo).accession_ids == baseline


def test_inventory_get_rejects_unknown_accession(repo_root: Path) -> None:
    with pytest.raises(KeyError, match="missing-accession"):
        load_source_inventory(repo_root).get("missing-accession")


def test_loading_real_package_is_read_only(package_root: Path, repo_root: Path) -> None:
    before = _hash_package_files(package_root)
    load_source_inventory(repo_root)
    assert _hash_package_files(package_root) == before


def test_public_error_type_is_a_value_error() -> None:
    assert issubclass(SourceInventoryError, ValueError)


def test_missing_repository_root_is_wrapped_without_machine_path(tmp_path: Path) -> None:
    missing = tmp_path / "absent"
    with pytest.raises(SourceInventoryError) as caught:
        load_source_inventory(missing)
    assert caught.value.code == "missing-repository-root"
    assert str(missing) not in str(caught.value)


def test_repository_root_symlink_loop_is_wrapped(tmp_path: Path) -> None:
    loop = tmp_path / "loop"
    loop.symlink_to(loop.name)
    with pytest.raises(SourceInventoryError) as caught:
        load_source_inventory(loop)
    assert caught.value.code == "missing-repository-root"
    assert str(tmp_path) not in str(caught.value)


def test_compact_only_id_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        family, path, details, _ = _detail_for(
            repo, manifest, "zhws-yisizhan-2-r854559"
        )
        details.pop(0)
        family["accession_count"] -= 1
        _write_json(path, details)
        _save_manifest(repo, manifest)

    _assert_error(mutable_repo, "missing-detailed-record", mutate)


def test_detailed_only_id_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        family, path, details, detail = _detail_for(
            repo, manifest, "zhws-yisizhan-2-r854559"
        )
        extra = dict(detail)
        extra["accession_id"] = "zhws-yisizhan-extra-r1"
        details.append(extra)
        family["accession_count"] += 1
        _write_json(path, details)
        _save_manifest(repo, manifest)

    _assert_error(mutable_repo, "unindexed-detailed-record", mutate)


def test_duplicate_compact_accession_id_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        manifest["accessions"].append(dict(manifest["accessions"][0]))
        _save_manifest(repo, manifest)

    _assert_error(mutable_repo, "duplicate-accession-id", mutate)


def test_untrusted_accession_id_cannot_leak_machine_path(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        manifest["accessions"][0]["accession_id"] = "/workspace/private/object"
        _save_manifest(repo, manifest)

    error = _assert_error(mutable_repo, "missing-detailed-record", mutate)
    assert error.accession_id == "<invalid-identifier>"
    assert "/workspace" not in str(error)


def test_duplicate_detailed_accession_across_families_is_rejected(
    mutable_repo: Path,
) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        _, _, _, source = _detail_for(
            repo, manifest, "zhws-yisizhan-2-r854559"
        )
        target_family = _family_for(manifest, "houhanji")
        target_path = _family_file(repo, target_family)
        target_details = _load_json(target_path)
        target_details.append(dict(source))
        target_family["accession_count"] += 1
        _write_json(target_path, target_details)
        _save_manifest(repo, manifest)

    _assert_error(mutable_repo, "duplicate-accession-id", mutate)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("page_title", "乙巳占/500"),
        ("oldid", 500),
        ("raw_path", "corpus/research_sources/related-wikisource/p0/x.wikitext"),
        ("raw_sha256", "0" * 64),
        ("raw_byte_count", 1),
        ("capture_status", "partial_with_reason"),
    ],
)
def test_shared_field_mismatch_is_rejected(
    mutable_repo: Path, field: str, replacement: object
) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        _, path, details, detail = _detail_for(
            repo, manifest, "zhws-yisizhan-5-r854562"
        )
        detail[field] = replacement
        _write_json(path, details)

    error = _assert_error(mutable_repo, "field-mismatch", mutate)
    assert error.field == field


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("oldid", 854_562.0),
        ("oldid", True),
        ("raw_byte_count", 31_158.0),
        ("raw_byte_count", True),
    ],
)
def test_shared_field_json_type_mismatch_is_rejected(
    mutable_repo: Path, field: str, replacement: object
) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        target = next(
            item
            for item in manifest["accessions"]
            if item["accession_id"] == "zhws-yisizhan-5-r854562"
        )
        target[field] = replacement
        _save_manifest(repo, manifest)

    error = _assert_error(mutable_repo, "field-mismatch", mutate)
    assert error.field == field


def test_family_membership_mismatch_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        target = next(
            item
            for item in manifest["accessions"]
            if item["accession_id"] == "zhws-yisizhan-5-r854562"
        )
        target["family_id"] = "houhanji"
        _save_manifest(repo, manifest)

    _assert_error(mutable_repo, "family-mismatch", mutate)


@pytest.mark.parametrize(
    ("field", "delta"),
    [
        ("family_count", 1),
        ("accession_count", 1),
        ("raw_file_count", 1),
        ("total_raw_byte_count", 1),
    ],
)
def test_global_count_mismatch_is_rejected(
    mutable_repo: Path, field: str, delta: int
) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        manifest[field] += delta
        _save_manifest(repo, manifest)

    error = _assert_error(mutable_repo, "count-mismatch", mutate)
    assert error.field == field


def test_family_declared_count_mismatch_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        manifest["families"][0]["accession_count"] += 1
        _save_manifest(repo, manifest)

    _assert_error(mutable_repo, "count-mismatch", mutate)


def test_duplicate_family_id_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        manifest["families"][1]["family_id"] = manifest["families"][0]["family_id"]
        _save_manifest(repo, manifest)

    _assert_error(mutable_repo, "duplicate-family-id", mutate)


def test_duplicate_metadata_path_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        manifest["families"][1]["accession_metadata_path"] = manifest["families"][0][
            "accession_metadata_path"
        ]
        _save_manifest(repo, manifest)

    _assert_error(mutable_repo, "duplicate-metadata-path", mutate)


def test_duplicate_raw_path_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        source = manifest["accessions"][0]
        target = manifest["accessions"][1]
        _, path, details, detail = _detail_for(repo, manifest, target["accession_id"])
        for field in ("raw_path", "raw_sha256", "raw_byte_count"):
            target[field] = source[field]
            detail[field] = source[field]
        _write_json(path, details)
        _save_manifest(repo, manifest)

    _assert_error(mutable_repo, "duplicate-raw-path", mutate)


def test_missing_raw_file_is_rejected_without_absolute_path(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        raw_path = repo / Path(manifest["accessions"][0]["raw_path"])
        raw_path.unlink()

    _assert_error(mutable_repo, "missing-raw-file", mutate)


def test_raw_byte_count_mismatch_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        raw_path = repo / Path(manifest["accessions"][0]["raw_path"])
        raw_path.write_bytes(raw_path.read_bytes() + b"x")

    _assert_error(mutable_repo, "raw-byte-count-mismatch", mutate)


def test_equal_length_raw_mutation_is_rejected_by_sha(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        raw_path = repo / Path(manifest["accessions"][0]["raw_path"])
        raw = bytearray(raw_path.read_bytes())
        raw[0] ^= 1
        raw_path.write_bytes(raw)

    _assert_error(mutable_repo, "raw-sha256-mismatch", mutate)


@pytest.mark.parametrize(
    "declared",
    [
        "/outside/accessions.json",
        "/workspace/private/accessions.json",
        "/tmp/private/accessions.json",
        "/Users/private/accessions.json",
        "C:\\private\\accessions.json",
        "\\\\server\\share\\accessions.json",
        "corpus/research_sources/related-wikisource/../outside.json",
    ],
)
def test_metadata_path_escape_is_rejected(
    mutable_repo: Path, declared: str
) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        manifest["families"][0]["accession_metadata_path"] = declared
        _save_manifest(repo, manifest)

    error = _assert_error(mutable_repo, "path-outside-package", mutate)
    for signature in ("/workspace", "/tmp", "/Users", "C:\\", "\\\\server"):
        assert signature not in str(error)


def test_metadata_symlink_escape_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        family = manifest["families"][0]
        source = _family_file(repo, family)
        outside = repo / "outside"
        outside.mkdir()
        shutil.copy2(source, outside / "accessions.json")
        link = repo / PACKAGE_RELATIVE / "escape"
        link.symlink_to(outside, target_is_directory=True)
        family["accession_metadata_path"] = (
            f"{PACKAGE_RELATIVE.as_posix()}/escape/accessions.json"
        )
        _save_manifest(repo, manifest)

    _assert_error(mutable_repo, "symlink-path-forbidden", mutate)


def test_manifest_symlink_is_rejected_even_when_target_remains_in_repo(
    mutable_repo: Path,
) -> None:
    manifest_path = mutable_repo / PACKAGE_RELATIVE / "accession-manifest.json"
    outside = mutable_repo / "manifest-copy.json"
    shutil.copy2(manifest_path, outside)
    manifest_path.unlink()
    manifest_path.symlink_to(outside)

    with pytest.raises(SourceInventoryError) as caught:
        load_source_inventory(mutable_repo)
    assert caught.value.code == "symlink-path-forbidden"
    assert str(mutable_repo) not in str(caught.value)


def test_internal_raw_symlink_alias_is_rejected(mutable_repo: Path) -> None:
    manifest = _manifest(mutable_repo)
    first = mutable_repo / Path(manifest["accessions"][0]["raw_path"])
    alias_target = first.parent / "unindexed-copy.wikitext"
    shutil.copy2(first, alias_target)
    first.unlink()
    first.symlink_to(alias_target.name)

    with pytest.raises(SourceInventoryError) as caught:
        load_source_inventory(mutable_repo)
    assert caught.value.code == "symlink-path-forbidden"


def test_symlink_loop_is_wrapped_as_inventory_error(mutable_repo: Path) -> None:
    manifest = _manifest(mutable_repo)
    raw_path = mutable_repo / Path(manifest["accessions"][0]["raw_path"])
    raw_path.unlink()
    raw_path.symlink_to(raw_path.name)

    with pytest.raises(SourceInventoryError) as caught:
        load_source_inventory(mutable_repo)
    assert caught.value.code == "symlink-path-forbidden"


def test_raw_symlink_escape_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        raw_path = repo / Path(manifest["accessions"][0]["raw_path"])
        outside = repo / "outside-raw.wikitext"
        shutil.copy2(raw_path, outside)
        raw_path.unlink()
        raw_path.symlink_to(outside)

    _assert_error(mutable_repo, "symlink-path-forbidden", mutate)


def test_unindexed_raw_file_is_rejected(mutable_repo: Path) -> None:
    orphan = mutable_repo / PACKAGE_RELATIVE / "p0/yisizhan/raw/orphan.wikitext"
    orphan.write_text("未登記原文", encoding="utf-8")

    with pytest.raises(SourceInventoryError) as caught:
        load_source_inventory(mutable_repo)
    assert caught.value.code == "raw-file-set-mismatch"
    assert "orphan.wikitext" in str(caught.value)


def test_malformed_manifest_json_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        (repo / PACKAGE_RELATIVE / "accession-manifest.json").write_text(
            "{", encoding="utf-8"
        )

    _assert_error(mutable_repo, "invalid-json", mutate)


def test_non_array_family_metadata_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        _write_json(_family_file(repo, manifest["families"][0]), {})

    _assert_error(mutable_repo, "invalid-shape", mutate)


def test_malformed_family_metadata_json_is_rejected(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        _family_file(repo, manifest["families"][0]).write_bytes(b"[\xff")

    error = _assert_error(mutable_repo, "invalid-json", mutate)
    assert "accessions.json" in error.field


def test_partial_capture_with_complete_raw_identity_is_replayed(
    mutable_repo: Path,
) -> None:
    manifest = _manifest(mutable_repo)
    accession_id = "zhws-yisizhan-5-r854562"
    compact = next(
        item for item in manifest["accessions"] if item["accession_id"] == accession_id
    )
    _, path, details, detail = _detail_for(mutable_repo, manifest, accession_id)
    compact["capture_status"] = "partial_with_reason"
    detail["capture_status"] = "partial_with_reason"
    detail["failure_reason"] = "fixed revision is a partial carrier capture"
    _write_json(path, details)
    _save_manifest(mutable_repo, manifest)

    item = load_source_inventory(mutable_repo).get(accession_id)
    assert item.capture_status.value == "partial_with_reason"
    assert item.raw_byte_count == 31_158


@pytest.mark.parametrize(
    "mutation_kind",
    ["complete_failure", "unavailable_raw", "partial_half_raw"],
)
def test_capture_status_truth_table_is_enforced(
    mutable_repo: Path, mutation_kind: str
) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        accession_id = "zhws-yisizhan-5-r854562"
        compact = next(
            item
            for item in manifest["accessions"]
            if item["accession_id"] == accession_id
        )
        _, path, details, detail = _detail_for(repo, manifest, accession_id)
        if mutation_kind == "complete_failure":
            detail["failure_reason"] = "contradiction"
        elif mutation_kind == "unavailable_raw":
            compact["capture_status"] = "unavailable"
            detail["capture_status"] = "unavailable"
            detail["failure_reason"] = "unavailable"
        else:
            compact["capture_status"] = "partial_with_reason"
            detail["capture_status"] = "partial_with_reason"
            detail["failure_reason"] = "partial"
            compact["raw_sha256"] = None
            detail["raw_sha256"] = None
        _write_json(path, details)
        _save_manifest(repo, manifest)

    _assert_error(mutable_repo, "invalid-detailed-record", mutate)


@pytest.mark.parametrize(
    "permanent_url",
    [
        "http://zh.wikisource.org/w/index.php?title=乙巳占/5&oldid=854562",
        "https://attacker.example/w/index.php?title=乙巳占/5&oldid=854562",
        "https://zh.wikisource.org@attacker.example/w/index.php?title=乙巳占/5&oldid=854562",
        "https://zh.wikisource.org/w/index.php?title=乙巳占/50&oldid=854562",
        "https://zh.wikisource.org/w/index.php?title=乙巳占/5&oldid=854562&oldid=854562",
    ],
)
def test_revision_url_boundary_is_enforced(
    mutable_repo: Path, permanent_url: str
) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        _, path, details, detail = _detail_for(
            repo, manifest, "zhws-yisizhan-5-r854562"
        )
        detail["permanent_url"] = permanent_url
        _write_json(path, details)

    _assert_error(mutable_repo, "invalid-detailed-record", mutate)


def test_invalid_detailed_case_order_is_wrapped(mutable_repo: Path) -> None:
    def mutate(repo: Path) -> None:
        manifest = _manifest(repo)
        _, path, details, detail = _detail_for(
            repo, manifest, "zhws-yisizhan-5-r854562"
        )
        detail["core14_cases"] = ["C13", "C09"]
        _write_json(path, details)

    error = _assert_error(mutable_repo, "invalid-detailed-record", mutate)
    assert error.field == "core14_cases"
