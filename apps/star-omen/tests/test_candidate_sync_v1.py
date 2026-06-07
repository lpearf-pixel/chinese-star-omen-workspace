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
    monkeypatch.setattr(KBSearchRetriever, "retrieve", lambda self, *args, **kwargs: {"hits": [], "exact_hits": [], "related_hits": [], "query_variants": self._query_variants(args[0]), "query_mode": "evidence"})
    off = KBSearchRetriever().two_stage_retrieve("荧惑守心", filters={"book_id": "kaiyuan_zhanjing"})
    assert all(h.get("source_namespace") != "downstream_generated" for h in off["stage2"].get("primary_candidates", []))
    monkeypatch.setenv("KB_ENABLE_CANDIDATE_OVERLAY", "true")
    reload_settings()
    on = KBSearchRetriever().two_stage_retrieve("荧惑守心", filters={"book_id": "kaiyuan_zhanjing"})
    candidates = on["stage2"].get("primary_candidates", [])
    assert any(h.get("source_namespace") == "downstream_generated" for h in candidates)
    assert all(h.get("evidence_level") != "candidate" for h in on["stage2"].get("exact_hits", []))
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
    monkeypatch.setattr(cc.KBSearchRetriever, "get_upstream_meta", lambda self: {"corpus_version": "v", "ingest_run_id": "run", "source_manifest_hash": "sha256:" + "b"*64})
    monkeypatch.setattr(cc, "_retrieve_hits", lambda base_url, term: [{"content_hash": item["content_hash"]}])
    out = cc.sync_upstream_status("kaiyuan_zhanjing", root, "http://upstream")
    assert out["updated"]["merged"] == 1
    monkeypatch.setattr(cc, "_retrieve_hits", lambda base_url, term: [{"content_hash": "sha256:" + "c"*64, "snippet": "other"}])
    out = cc.sync_upstream_status("kaiyuan_zhanjing", root, "http://upstream")
    assert out["updated"]["needs_review"] == 1
    source.write_text("卷三十一\n\n不含原锚点。\n", encoding="utf-8")
    out = cc.sync_upstream_status("kaiyuan_zhanjing", root, "http://upstream")
    assert out["updated"]["stale"] == 1
