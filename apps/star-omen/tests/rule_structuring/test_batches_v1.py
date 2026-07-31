from __future__ import annotations

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.rule_structuring.batches import (
    BatchCheckpointV1,
    BatchError,
    canonical_batch_bytes,
    plan_batches,
    resume_batch,
    write_checkpoint_no_overwrite,
)
from src.rule_structuring.passage_inventory import (
    PassageInventoryV1,
    build_rule_passage_inventory,
    canonical_inventory_bytes,
    compare_source_fingerprint,
)


TEXT = """# 五星占

<pb:KR3g0018_WYG_031-17a>

荧惑守心，主君忧。

太白入昴，兵起。
"""


def kb_root(tmp_path: Path) -> Path:
    root = tmp_path / "kb"
    volume = root / "古籍/唐開元占經/分卷/KR3g0018_031.md"
    volume.parent.mkdir(parents=True)
    volume.write_text(TEXT, encoding="utf-8")
    return root


def test_inventory_is_path_safe_deterministic_and_strict(tmp_path: Path) -> None:
    root = kb_root(tmp_path)
    first = build_rule_passage_inventory(root)
    second = build_rule_passage_inventory(root)

    assert canonical_inventory_bytes(first) == canonical_inventory_bytes(second)
    assert first.schema_version == "rule-passage-inventory/v1"
    assert len(first.passages) == 2
    assert all(not item.source_path.startswith("/") for item in first.passages)
    assert all(
        item.source_fingerprint == first.source_fingerprint
        for item in first.passages
    )
    payload = first.model_dump(mode="json")
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        PassageInventoryV1.model_validate(payload)


def test_inventory_rejects_symlinked_primary_source(tmp_path: Path) -> None:
    root = tmp_path / "kb"
    target = tmp_path / "outside.md"
    target.write_text(TEXT, encoding="utf-8")
    link = root / "古籍/唐開元占經/分卷/KR3g0018_031.md"
    link.parent.mkdir(parents=True)
    link.symlink_to(target)

    with pytest.raises(ValueError, match="symlink"):
        build_rule_passage_inventory(root)


def test_source_fingerprint_comparison_reports_invalidated_passage(tmp_path: Path) -> None:
    root = kb_root(tmp_path)
    previous = build_rule_passage_inventory(root)
    source = root / "古籍/唐開元占經/分卷/KR3g0018_031.md"
    source.write_text(TEXT.replace("主君忧", "兵起"), encoding="utf-8")
    current = build_rule_passage_inventory(root)

    report = compare_source_fingerprint(previous, current)

    assert report.status == "source_changed"
    assert report.previous_source_fingerprint == previous.source_fingerprint
    assert report.current_source_fingerprint == current.source_fingerprint
    assert report.changed


def test_batch_plan_is_stable_bounded_and_input_order_independent(tmp_path: Path) -> None:
    inventory = build_rule_passage_inventory(kb_root(tmp_path))
    reversed_inventory = inventory.model_copy(
        update={"passages": list(reversed(inventory.passages))}
    )

    first = plan_batches(inventory, batch_size=100)
    second = plan_batches(reversed_inventory, batch_size=100)

    assert first == second
    assert canonical_batch_bytes(first) == canonical_batch_bytes(second)
    assert first.batch_size == 100
    assert first.batches[0].batch_id.startswith("batch:sha256:")
    with pytest.raises(BatchError, match="batch_size"):
        plan_batches(inventory, batch_size=99)
    with pytest.raises(BatchError, match="batch_size"):
        plan_batches(inventory, batch_size=501)


def test_resume_rejects_tamper_and_is_idempotent(tmp_path: Path) -> None:
    inventory = build_rule_passage_inventory(kb_root(tmp_path))
    batch = plan_batches(inventory, batch_size=100).batches[0]
    checkpoint = BatchCheckpointV1.new(batch)
    first_id = batch.passage_ids[0]
    checkpoint = checkpoint.with_completed(first_id, "a" * 64)

    assert resume_batch(batch, checkpoint) == resume_batch(batch, checkpoint)
    payload = checkpoint.model_dump(mode="json")
    payload["batch_id"] = "batch:sha256:" + "f" * 64
    with pytest.raises((ValidationError, BatchError)):
        resume_batch(batch, BatchCheckpointV1.model_validate(payload))

    duplicate = deepcopy(checkpoint.model_dump(mode="json"))
    duplicate["failed"].append(
        {"passage_id": first_id, "reason_code": "failed", "detail": "duplicate"}
    )
    with pytest.raises(ValidationError, match="disjoint"):
        BatchCheckpointV1.model_validate(duplicate)


def test_failed_deferred_and_finalize_cover_batch_exactly(tmp_path: Path) -> None:
    inventory = build_rule_passage_inventory(kb_root(tmp_path))
    batch = plan_batches(inventory, batch_size=100).batches[0]
    checkpoint = BatchCheckpointV1.new(batch)
    checkpoint = checkpoint.with_failed(
        batch, batch.passage_ids[0], "parse_failed", "synthetic failure"
    )
    checkpoint = checkpoint.with_deferred(
        batch, batch.passage_ids[1], "needs_review", "ambiguous wording"
    )
    checkpoint = checkpoint.finalize(batch)

    state = resume_batch(batch, checkpoint)
    assert state.status == "completed"
    assert state.remaining_passage_ids == ()


def test_checkpoint_publication_is_no_overwrite(tmp_path: Path) -> None:
    inventory = build_rule_passage_inventory(kb_root(tmp_path))
    batch = plan_batches(inventory, batch_size=100).batches[0]
    checkpoint = BatchCheckpointV1.new(batch)
    output = tmp_path / "checkpoint.json"

    write_checkpoint_no_overwrite(output, checkpoint)
    original = output.read_bytes()
    with pytest.raises(BatchError, match="output_exists"):
        write_checkpoint_no_overwrite(output, checkpoint)
    assert output.read_bytes() == original


def test_concurrent_checkpoint_publication_has_one_winner(tmp_path: Path) -> None:
    inventory = build_rule_passage_inventory(kb_root(tmp_path))
    batch = plan_batches(inventory, batch_size=100).batches[0]
    checkpoint = BatchCheckpointV1.new(batch)
    output = tmp_path / "concurrent-checkpoint.json"

    def publish() -> str:
        try:
            write_checkpoint_no_overwrite(output, checkpoint)
            return "published"
        except BatchError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: publish(), range(2)))

    assert sorted(results) == ["output_exists", "published"]
    assert output.read_bytes() == canonical_batch_bytes(checkpoint)
