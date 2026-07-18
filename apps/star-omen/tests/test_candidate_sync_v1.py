from pathlib import Path

import yaml

from src.config.settings import reload_settings
from src.candidate_cards import generate_candidate_cards
from src.connectors.candidate_overlay import overlay_hits
from src.connectors.kb_search_retriever import KBSearchRetriever


def _source(tmp_path: Path) -> Path:
    path = tmp_path / "古籍" / "唐開元占經" / "分卷" / "KR3g0018_031.md"
    path.parent.mkdir(parents=True)
    path.write_text("卷三十一\n\n熒惑守心，天下兵起。\n", encoding="utf-8")
    return path


def test_generate_candidate_card_manifest(monkeypatch, tmp_path):
    _source(tmp_path)
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    monkeypatch.setenv("KB_SOURCES_ROOT", str(tmp_path))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "false")
    reload_settings()
    out_dir = tmp_path / "generated_candidates" / "extract_cards" / "kaiyuan_zhanjing"
    result = generate_candidate_cards("荧惑守心", "kaiyuan_zhanjing", out_dir)
    assert result["generated"]
    manifest = out_dir / "candidate_manifest.json"
    assert manifest.exists()
    card = next(out_dir.glob("*.md"))
    fm = yaml.safe_load(card.read_text(encoding="utf-8").split("---", 2)[1])
    assert fm["schema_version"] == "candidate-card/v1"
    assert fm["evidence_level"] == "candidate"
    assert fm["source_namespace"] == "downstream_generated"
    assert fm["content_hash"].startswith("sha256:")
    assert "熒惑守心" in card.read_text(encoding="utf-8")


def test_overlay_default_and_enabled(monkeypatch, tmp_path):
    _source(tmp_path)
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    monkeypatch.setenv("KB_SOURCES_ROOT", str(tmp_path))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "false")
    reload_settings()
    root = tmp_path / "generated_candidates"
    out_dir = root / "extract_cards" / "kaiyuan_zhanjing"
    generate_candidate_cards("荧惑守心", "kaiyuan_zhanjing", out_dir)
    assert overlay_hits(root, "荧惑守心", book_id="kaiyuan_zhanjing")
    monkeypatch.setenv("KB_ENABLE_CANDIDATE_OVERLAY", "false")
    monkeypatch.setenv("KB_CANDIDATE_OVERLAY_ROOT", str(root))
    reload_settings()
    monkeypatch.setattr(
        KBSearchRetriever,
        "retrieve",
        lambda self, *args, **kwargs: {
            "hits": [],
            "exact_hits": [],
            "related_hits": [],
            "query_variants": self._query_variants(args[0]),
            "query_mode": "evidence",
        },
    )
    off = KBSearchRetriever().two_stage_retrieve(
        "荧惑守心",
        filters={"book_id": "kaiyuan_zhanjing"},
    )
    assert off["stage2"].get("candidate_overlay_hits", []) == []
    assert all(
        hit.get("source_namespace") != "downstream_generated"
        for hit in off["stage2"].get("primary_candidates", [])
    )

    monkeypatch.setenv("KB_ENABLE_CANDIDATE_OVERLAY", "true")
    reload_settings()
    on = KBSearchRetriever().two_stage_retrieve(
        "荧惑守心",
        filters={"book_id": "kaiyuan_zhanjing"},
    )
    overlay = on["stage2"].get("candidate_overlay_hits", [])
    assert any(
        hit.get("source_namespace") == "downstream_generated"
        for hit in overlay
    )
    assert all(hit.get("status") == "candidate_only" for hit in overlay)
    assert all(
        hit.get("source_namespace") != "downstream_generated"
        for hit in on["stage2"].get("primary_candidates", [])
    )
    assert all(
        hit.get("evidence_level") != "candidate"
        for hit in on["stage2"].get("exact_hits", [])
    )
    monkeypatch.setenv("KB_ENABLE_CANDIDATE_OVERLAY", "false")
    reload_settings()


def test_sync_status_marks_merged_needs_review_and_stale(monkeypatch, tmp_path):
    source = _source(tmp_path)
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    monkeypatch.setenv("KB_SOURCES_ROOT", str(tmp_path))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "false")
    reload_settings()
    root = tmp_path / "generated_candidates"
    out_dir = root / "extract_cards" / "kaiyuan_zhanjing"
    generate_candidate_cards("荧惑守心", "kaiyuan_zhanjing", out_dir)
    import src.candidate_cards as cc

    manifest_path = out_dir / "candidate_manifest.json"
    import json

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    item = manifest["items"][0]
    monkeypatch.setattr(
        cc.KBSearchRetriever,
        "get_upstream_meta",
        lambda self: {
            "meta_status": "ok",
            "corpus_version": "v",
            "ingest_run_id": "run",
            "source_manifest_hash": "sha256:" + "b" * 64,
            "collection": "local_kb_kaiyuan_v2",
        },
    )

    response = {
        "hits": [
            {
                "card_type": "extract_card",
                "content_hash": item["content_hash"],
                "source_locator": item["source_locator"],
            }
        ]
    }
    calls = []

    def fake_retrieve(self, query, **kwargs):
        calls.append({"query": query, **kwargs})
        return response

    monkeypatch.setattr(cc.KBSearchRetriever, "retrieve", fake_retrieve)

    out = cc.sync_upstream_status(
        "kaiyuan_zhanjing",
        root,
        "http://upstream",
    )
    assert out["updated"]["merged"] == 1
    assert calls[-1]["filters"] == {"kb_book_id": "kaiyuan_zhanjing"}
    assert calls[-1]["retrieval_stage"] == "structured_recall"
    assert calls[-1]["card_types"] == ["extract_card"]

    response["hits"] = [
        {
            "card_type": "extract_card",
            "content_hash": "sha256:" + "c" * 64,
            "source_locator": item["source_locator"],
            "snippet": "other",
        }
    ]
    out = cc.sync_upstream_status(
        "kaiyuan_zhanjing",
        root,
        "http://upstream",
    )
    assert out["updated"]["needs_review"] == 1

    call_count = len(calls)
    source.write_text("卷三十一\n\n不含原锚点。\n", encoding="utf-8")
    out = cc.sync_upstream_status(
        "kaiyuan_zhanjing",
        root,
        "http://upstream",
    )
    assert out["updated"]["stale"] == 1
    assert len(calls) == call_count


def test_generate_candidate_from_direct_kaiyuanzhanjin_repo_layout(monkeypatch, tmp_path):
    source = tmp_path / "kaiyuanzhanjin"
    (source / "分卷").mkdir(parents=True)
    (source / "分卷" / "KR3g0018_031.md").write_text(
        "卷三十一\n\n熒惑守心，天下兵起。\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    monkeypatch.setenv("KB_SOURCES_ROOT", str(source))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "false")
    reload_settings()
    out_dir = tmp_path / "generated_candidates" / "extract_cards" / "kaiyuan_zhanjing"

    result = generate_candidate_cards("荧惑守心", "kaiyuan_zhanjing", out_dir)

    assert result["generated"]
    card = next(out_dir.glob("*.md"))
    fm = yaml.safe_load(card.read_text(encoding="utf-8").split("---", 2)[1])
    assert fm["source_locator"] == "KR3g0018_031"
    assert fm["source_file"].endswith(
        "kaiyuanzhanjin/分卷/KR3g0018_031.md"
    )
    assert fm["kb_book_id"] == "kaiyuan_zhanjing"


def test_generate_candidate_fulltext_filename_is_ascii_safe(monkeypatch, tmp_path):
    source = tmp_path / "古籍" / "唐開元占經"
    source.mkdir(parents=True)
    (source / "唐開元占經-全文合併版.md").write_text(
        "熒惑守心，天下兵起。\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    monkeypatch.setenv("KB_SOURCES_ROOT", str(tmp_path))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "false")
    reload_settings()
    out_dir = tmp_path / "generated_candidates" / "extract_cards" / "kaiyuan_zhanjing"

    result = generate_candidate_cards("荧惑守心", "kaiyuan_zhanjing", out_dir)

    assert len(result["generated"]) == 1
    generated = Path(result["generated"][0])
    assert generated.name == "yinghuo_shouxin.fulltext.no-page.0.md"
    fm = yaml.safe_load(generated.read_text(encoding="utf-8").split("---", 2)[1])
    assert fm["source_locator"] == "fulltext"
    assert fm["source_file"].endswith(
        "唐開元占經/唐開元占經-全文合併版.md"
    )


def test_generate_candidate_match_offset_uses_original_text_index(monkeypatch, tmp_path):
    text = "序  \n熒 惑 守 心，天下兵起。\n"
    source = tmp_path / "古籍" / "唐開元占經" / "分卷" / "KR3g0018_031.md"
    source.parent.mkdir(parents=True)
    source.write_text(text, encoding="utf-8")
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    monkeypatch.setenv("KB_SOURCES_ROOT", str(tmp_path))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "false")
    reload_settings()
    out_dir = tmp_path / "generated_candidates" / "extract_cards" / "kaiyuan_zhanjing"

    generate_candidate_cards("荧惑守心", "kaiyuan_zhanjing", out_dir)

    card = next(out_dir.glob("*.md"))
    fm = yaml.safe_load(card.read_text(encoding="utf-8").split("---", 2)[1])
    assert fm["match_offset"] == text.index("熒")
    assert "熒 惑 守 心" in fm["anchor_text"]


def test_generate_candidate_clusters_exact_matches_by_page(monkeypatch, tmp_path):
    source = tmp_path / "古籍" / "唐開元占經" / "分卷" / "KR3g0018_031.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        "# 唐開元占經 卷31\n\n　　　熒惑犯心五\n"
        "<pb:KR3g0018_WYG_031-17a>\n熒惑守心，一。又曰熒惑守心，二。\n"
        "<pb:KR3g0018_WYG_031-17b>\n熒惑守心，三。\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    monkeypatch.setenv("KB_SOURCES_ROOT", str(tmp_path))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "false")
    reload_settings()
    out_dir = tmp_path / "generated_candidates" / "extract_cards" / "kaiyuan_zhanjing"

    result = generate_candidate_cards("荧惑守心", "kaiyuan_zhanjing", out_dir)

    assert len(result["generated"]) == 2
    cards = [
        yaml.safe_load(
            Path(path).read_text(encoding="utf-8").split("---", 2)[1]
        )
        for path in result["generated"]
    ]
    assert [card["page_marker"] for card in cards] == [
        "KR3g0018_WYG_031-17a",
        "KR3g0018_WYG_031-17b",
    ]
    assert cards[0]["match_count"] == 2
    assert cards[0]["heading_path"][-1] == "熒惑犯心五"
