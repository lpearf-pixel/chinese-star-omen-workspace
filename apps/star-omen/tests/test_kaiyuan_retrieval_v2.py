from pathlib import Path

import src.connectors.primary_file_scanner as scanner_module
import src.connectors.primary_passage_cache as cache_module
from src.config.settings import reload_settings
from src.connectors.kb_search_retriever import KBSearchRetriever
from src.connectors.primary_file_scanner import source_locator
from src.connectors.primary_passage_cache import PrimaryPassageCache


def _configure_sources(monkeypatch, root: Path) -> None:
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    monkeypatch.setenv("KB_SOURCES_ROOT", str(root))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "false")
    reload_settings()


def test_retrieve_payload_carries_v2_contract_and_canonical_book_id(monkeypatch):
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
        retrieval_stage="primary_evidence",
        card_types=["fenjuan", "fulltext"],
        literal_first=True,
    )

    assert captured["schema_version"] == "kb-retrieve/v2"
    assert captured["top_k"] == 8
    assert captured["retrieval_stage"] == "primary_evidence"
    assert captured["card_types"] == ["fenjuan", "fulltext"]
    assert captured["filters"] == {"kb_book_id": "kaiyuan_zhanjing"}
    assert "limit" not in captured


def test_wire_payload_removes_legacy_book_id_alias():
    payload = KBSearchRetriever._wire_payload(
        {
            "query": "荧惑守心",
            "filters": {
                "book_id": "kaiyuan_zhanjing",
                "kb_book_id": "kaiyuan_zhanjing",
            },
        }
    )
    assert payload is not None
    assert payload["filters"] == {"kb_book_id": "kaiyuan_zhanjing"}


def test_explicit_query_mode_controls_reranking(monkeypatch):
    def fake_request(self, method, path, **kwargs):
        return {
            "hits": [
                {
                    "chunk_id": "e1",
                    "title": "荧惑",
                    "path": "/docs/古籍/唐開元占經/术语卡片/熒惑.md",
                    "snippet": "荧惑",
                    "card_type": "term_card",
                }
            ]
        }

    monkeypatch.setattr(KBSearchRetriever, "_request", fake_request)
    retriever = KBSearchRetriever(base_url="http://127.0.0.1:8008", api_key="k")
    result = retriever.retrieve("荧惑", query_mode="evidence")
    assert result["query_mode"] == "evidence"
    assert result["exact_hits"][0]["chunk_id"] == "e1"


def test_fulltext_page_marker_maps_to_canonical_volume_locator():
    assert source_locator(
        "/docs/古籍/唐開元占經/唐開元占經-全文合併版.md",
        "KR3g0018_WYG_031-17a",
    ) == "KR3g0018_031"


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
    assert hits[0]["source_locator"] == "KR3g0018_031"
    assert hits[0]["heading_path"][-1] == "熒惑犯心五"
    assert "熒 惑 守 心" in hits[0]["snippet"]
    assert stats["matched_headings"] == ["熒惑犯心五"]


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


def test_repeated_filesystem_scan_reuses_cached_passage_parse(monkeypatch, tmp_path):
    corpus = tmp_path / "古籍" / "唐開元占經" / "分卷"
    corpus.mkdir(parents=True)
    (corpus / "KR3g0018_031.md").write_text(
        "# 唐開元占經 卷31\n\n## 熒惑占\n"
        "<pb:KR3g0018_WYG_031-17a>\n熒惑守心，天下兵起。",
        encoding="utf-8",
    )
    _configure_sources(monkeypatch, tmp_path)
    isolated_cache = PrimaryPassageCache()
    monkeypatch.setattr(scanner_module, "primary_passage_cache", isolated_cache)
    real_parser = cache_module.parse_kaiyuan_passages
    calls = 0

    def counting_parser(*args, **kwargs):
        nonlocal calls
        calls += 1
        return real_parser(*args, **kwargs)

    monkeypatch.setattr(cache_module, "parse_kaiyuan_passages", counting_parser)
    retriever = KBSearchRetriever(base_url="http://127.0.0.1:8008", api_key="k")

    first, first_stats = retriever._scan_primary_files(
        "荧惑守心", book_id="kaiyuan_zhanjing", mode="evidence", limit=3
    )
    second, second_stats = retriever._scan_primary_files(
        "荧惑守心", book_id="kaiyuan_zhanjing", mode="evidence", limit=3
    )

    assert calls == 1
    assert second == first
    assert second_stats == first_stats
    assert first[0]["page_marker"] == "KR3g0018_WYG_031-17a"
    assert first[0]["heading_path"][-1] == "熒惑占"
