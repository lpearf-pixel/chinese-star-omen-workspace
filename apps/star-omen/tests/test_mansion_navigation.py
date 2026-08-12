from __future__ import annotations

import re
from pathlib import Path

import yaml

from src.video_pipeline.asterisms import load_asterism_catalog


APP_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = APP_ROOT / "data" / "sources" / "古籍" / "唐開元占經"
OVERVIEW_PATH = SOURCE_ROOT / "导航" / "二十八宿總覽.md"
CARD_ROOT = SOURCE_ROOT / "逐宿卡"
BI_CARD_PATH = CARD_ROOT / "畢宿.md"
CATALOG_PATH = APP_ROOT / "data" / "video_pipeline" / "asterism_catalog_v1.yaml"


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1])


def test_twenty_eight_mansion_overview_links_resolve_to_existing_cards() -> None:
    text = OVERVIEW_PATH.read_text(encoding="utf-8")
    targets = [
        target
        for target in re.findall(r"\[\[逐宿卡/([^\]]+)\]\]", text)
        if not target.endswith("七宿")
    ]

    assert len(targets) == 28
    assert len(set(targets)) == 28
    assert all((CARD_ROOT / f"{target}.md").is_file() for target in targets)


def test_bi_navigation_status_is_bound_to_the_scientific_catalog() -> None:
    metadata = frontmatter(BI_CARD_PATH)
    catalog = load_asterism_catalog(CATALOG_PATH).catalog
    definition = catalog.asterism("bi-xiu")
    mansion = catalog.mansion("bi-xiu")
    status = metadata["scientific_catalog"]

    assert metadata["title"] == "畢宿"
    assert "毕宿" in metadata["aliases"]
    assert status == {
        "schema_version": "mansion-navigation-status/v1",
        "catalog_id": catalog.catalog_id,
        "catalog_version": catalog.catalog_version,
        "asterism_id": definition.asterism_id,
        "completeness_status": definition.completeness_status,
        "member_object_ids": definition.member_object_ids,
        "related_object_ids": definition.related_object_ids,
        "defining_star_object_id": definition.defining_star_object_id,
        "west_boundary_object_id": mansion.west_boundary_object_id,
        "east_boundary_object_id": mansion.east_boundary_object_id,
        "boundary_model": mansion.boundary_model,
        "coordinate_system": mansion.coordinate_system,
        "provenance_class": mansion.provenance_class,
        "source_refs": list(dict.fromkeys([*definition.source_refs, *mansion.source_refs])),
    }
