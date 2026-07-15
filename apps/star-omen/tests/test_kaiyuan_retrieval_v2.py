from pathlib import Path

from src.config.settings import reload_settings
from src.connectors.kb_search_retriever import KBSearchRetriever


def _configure_sources(monkeypatch, root: Path) -> None:
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    monkeypatch.setenv("KB_SOURCES_ROOT", str(root))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "false")
    reload_settings()


def test_retrieve_payload_carries_v2_limit_and_canonical_book_id(monkeypatch):
    captured = {}

    def fake_request(self, method, path, **kwargs):
        captured.update(kwargs["json_payload"])
        return {"hits": []}

    monkeypatch.setattr(KBSearchRetriever, "_request", fake_request)
    retriever = KBSearchRetriever(base_url="http://127.0.0.1:8008", api_key="k")
    retriever.retrieve(
        "荧惑守心",
        top_k=8,
        filters={"book_id": "kaiyuan_zhanjing"},
        query_mode="evidence",
        literal_first=True,
    )

    assert captured["top_k"] == 8
    assert captured["limit"] == 8
    assert captured["filters"]["kb_book_id"] == "kaiyuan_zhanjing"
    assert captured["filters"]["book_id"] == "kaiyuan_zhanjing"


def test_filesystem_fallback_returns_match_excerpt_and_fenjuan_first(monkeypatch, tmp_path):
    corpus = tmp_path / "古籍" / "唐開元占經"
    volume = corpus / "分卷" / "KR3g0018_031.md"
    volume.parent.mkdir(parents=True)
    volume.write_text(
        "# 唐開元占經 卷31\n\n　　　熒惑犯心五\n"
        "<pb:KR3g0018_WYG_031-17a>\n石氏曰熒 惑 守 心，天下兵起。\n",
        encoding="utf-8",
    )
    (corpus / "唐開元占經-全文合併版.md").write_text(
        volume.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _configure_sources(monkeypatch, tmp_path)
    retriever = KBSearchRetriever(base_url="http://127.0.0.1:8008", api_key="k")

    hits, stats = retriever._scan_primary_files(
        "荧惑守心",
        book_id="kaiyuan_zhanjing",
        mode="evidence",
        limit=8,
        query_variants=retriever._query_variants("荧惑守心"),
    )

    assert stats["files_scanned"] == 2
    assert len(hits) == 1
    assert hits[0]["card_type"] == "fenjuan"
    assert hits[0]["match_type"] == "exact_normalized"
    assert hits[0]["page_marker"] == "KR3g0018_WYG_031-17a"
    assert hits[0]["heading_path"][-1] == "熒惑犯心五"
    assert "熒 惑 守 心" in hits[0]["snippet"]
    assert stats["matched_headings"] == ["KR3g0018_031"]


def test_filesystem_fallback_scans_all_candidates_before_limit(monkeypatch, tmp_path):
    corpus = tmp_path / "古籍" / "唐開元占經"
    corpus.mkdir(parents=True)
    (corpus / "唐開元占經-全文合併版.md").write_text(
        "熒惑守心，旁證。",
        encoding="utf-8",
    )
    volume = corpus / "分卷" / "KR3g0018_031.md"
    volume.parent.mkdir()
    volume.write_text(
        "# 唐開元占經 卷31\n　　　熒惑犯心五\n"
        "<pb:KR3g0018_WYG_031-17a>\n熒惑守心，正證。",
        encoding="utf-8",
    )
    _configure_sources(monkeypatch, tmp_path)
    retriever = KBSearchRetriever(base_url="http://127.0.0.1:8008", api_key="k")

    hits, stats = retriever._scan_primary_files(
        "荧惑守心",
        book_id="kaiyuan_zhanjing",
        mode="evidence",
        limit=1,
    )

    assert stats["files_scanned"] == 2
    assert hits[0]["card_type"] == "fenjuan"
    assert hits[0]["source_locator"] == "KR3g0018_031"
