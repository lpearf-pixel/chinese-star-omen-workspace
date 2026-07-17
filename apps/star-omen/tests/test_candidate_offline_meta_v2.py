from __future__ import annotations

from pathlib import Path

import yaml

from src.config.settings import reload_settings
from src.candidate_cards import generate_candidate_cards
from src.connectors.kb_search_retriever import KBSearchError, KBSearchRetriever


def test_candidate_generation_records_unavailable_meta_without_network(monkeypatch, tmp_path: Path):
    source = tmp_path / "古籍" / "唐開元占經" / "分卷" / "KR3g0018_031.md"
    source.parent.mkdir(parents=True)
    source.write_text("卷三十一\n\n熒惑守心，天下兵起。\n", encoding="utf-8")

    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    monkeypatch.setenv("KB_SOURCES_ROOT", str(tmp_path))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "false")
    reload_settings()
    monkeypatch.setattr(
        KBSearchRetriever,
        "get_upstream_meta",
        lambda self: (_ for _ in ()).throw(KBSearchError("offline")),
    )

    out_dir = tmp_path / "generated_candidates" / "extract_cards" / "kaiyuan_zhanjing"
    result = generate_candidate_cards("荧惑守心", "kaiyuan_zhanjing", out_dir)

    assert result["generated"]
    assert result["upstream_meta"]["meta_status"] == "unavailable"
    assert result["upstream_meta"]["error_code"] == "UPSTREAM_META_UNAVAILABLE"

    card = next(out_dir.glob("*.md"))
    metadata = yaml.safe_load(card.read_text(encoding="utf-8").split("---", 2)[1])
    assert metadata["base_meta_status"] == "unavailable"
    assert metadata["base_corpus_version"] == "unavailable"
    assert metadata["base_ingest_run_id"] == "unavailable"
