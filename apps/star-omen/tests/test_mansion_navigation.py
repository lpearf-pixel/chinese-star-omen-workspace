from __future__ import annotations

import re
from pathlib import Path

import yaml

from src.video_pipeline.asterisms import load_asterism_catalog


APP_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = APP_ROOT / "data" / "sources" / "古籍" / "唐開元占經"
OVERVIEW_PATH = SOURCE_ROOT / "导航" / "二十八宿總覽.md"
CARD_ROOT = SOURCE_ROOT / "逐宿卡"
CATALOG_PATH = APP_ROOT / "data" / "video_pipeline" / "asterism_catalog_v1.yaml"


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1])


def overview_targets() -> list[str]:
    text = OVERVIEW_PATH.read_text(encoding="utf-8")
    return [
        target
        for target in re.findall(r"\[\[逐宿卡/([^\]]+)\]\]", text)
        if not target.endswith("七宿")
    ]


def expected_status(catalog, definition) -> dict:
    mansion = catalog.mansion(definition.asterism_id)
    return {
        "schema_version": "mansion-navigation-status/v1",
        "catalog_id": catalog.catalog_id,
        "catalog_version": catalog.catalog_version,
        "asterism_id": definition.asterism_id,
        "sequence_index": mansion.sequence_index,
        "completeness_status": definition.completeness_status,
        "member_object_ids": definition.member_object_ids,
        "related_object_ids": definition.related_object_ids,
        "ambiguous_member_object_ids": [
            object_id
            for object_id in definition.member_object_ids
            if catalog.entry(object_id).editorial_status == "ambiguous"
        ],
        "defining_star_object_id": definition.defining_star_object_id,
        "line_segments": definition.line_segments,
        "west_boundary_object_id": mansion.west_boundary_object_id,
        "east_boundary_object_id": mansion.east_boundary_object_id,
        "boundary_model": mansion.boundary_model,
        "coordinate_system": mansion.coordinate_system,
        "provenance_class": mansion.provenance_class,
        "source_refs": list(
            dict.fromkeys([*definition.source_refs, *mansion.source_refs])
        ),
    }


def test_twenty_eight_mansion_overview_links_resolve_to_existing_cards() -> None:
    targets = overview_targets()

    assert len(targets) == 28
    assert len(set(targets)) == 28
    assert all((CARD_ROOT / f"{target}.md").is_file() for target in targets)


def test_all_mansion_cards_are_bound_to_the_scientific_catalog() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog
    targets = overview_targets()
    cards = [
        (CARD_ROOT / f"{target}.md", frontmatter(CARD_ROOT / f"{target}.md"))
        for target in targets
    ]
    definitions = [catalog.asterism(metadata["title"]) for _, metadata in cards]
    expected_mansions = sorted(
        catalog.lunar_mansions, key=lambda item: item.sequence_index
    )

    assert [definition.asterism_id for definition in definitions] == [
        mansion.mansion_id for mansion in expected_mansions
    ]
    missing_status = [
        path.name for path, metadata in cards if "scientific_catalog" not in metadata
    ]
    assert missing_status == []

    for (path, metadata), definition in zip(cards, definitions, strict=True):
        expected_aliases = [
            name
            for name in [definition.canonical_chinese_name, *definition.aliases]
            if name != metadata["title"]
        ]
        assert metadata["aliases"] == list(dict.fromkeys(expected_aliases))
        assert all(catalog.asterism(alias) == definition for alias in metadata["aliases"])
        assert metadata["scientific_catalog"] == expected_status(catalog, definition)
        assert path.read_text(encoding="utf-8").count(
            "## 科学目录状态（现代映射）"
        ) == 1
