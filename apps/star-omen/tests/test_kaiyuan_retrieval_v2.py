import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import src.connectors.primary_file_scanner as scanner_module
import src.connectors.primary_passage_cache as cache_module
from src.config.settings import reload_settings
from src.connectors.kb_search_retriever import KBSearchRetriever
from src.connectors.primary_file_scanner import scan_primary_files, source_locator
from src.connectors.primary_passage_cache import (
    PrimaryPassageCache,
    build_primary_source_snapshot,
)
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalKBSourceSnapshotV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
    canonical_contract_sha256,
)
from src.video_pipeline.feedback_loop.source_snapshot_v1 import LocalKBSourceAccessor


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


class _CountingByteLoader:
    def __init__(self, root: Path, relative_paths: tuple[str, ...]) -> None:
        self.root = root
        self._relative_paths = relative_paths
        self.calls: list[str] = []

    def relative_paths(self) -> tuple[str, ...]:
        return self._relative_paths

    def load(self, path, *, card_type, kb_book_id, book_title):
        relative_path = Path(path).as_posix()
        self.calls.append(relative_path)
        source = self.root / relative_path
        return build_primary_source_snapshot(
            source.read_bytes(),
            path=source,
            mtime_ns=77,
            card_type=card_type,
            kb_book_id=kb_book_id,
            book_title=book_title,
        )


def test_strict_scanner_uses_only_loader_inventory_and_exact_passage_boundary(
    monkeypatch, tmp_path: Path
):
    relative_path = "古籍/唐開元占經/分卷/KR3g0018_031.md"
    source = tmp_path / relative_path
    source.parent.mkdir(parents=True)
    source.write_text(
        "# 唐開元占經\n"
        "<pb:KR3g0018_WYG_031-17a>\n"
        "前段無關。\n\n"
        "石氏曰畢宿主兵。\n",
        encoding="utf-8",
    )
    loader = _CountingByteLoader(tmp_path, (relative_path,))

    def forbidden_rglob(*_args, **_kwargs):
        raise AssertionError("strict scanner must not enumerate the live root")

    def forbidden_cache(*_args, **_kwargs):
        raise AssertionError("strict scanner must not use the pathname cache")

    monkeypatch.setattr(Path, "rglob", forbidden_rglob)
    monkeypatch.setattr(scanner_module.primary_passage_cache, "load", forbidden_cache)

    hits, stats = scan_primary_files(
        SimpleNamespace(
            kb_sources_root=tmp_path,
            kb_enable_obsidian_source=False,
            kb_obsidian_root=tmp_path / "unused",
        ),
        "畢宿",
        book_id="kaiyuan_zhanjing",
        mode="evidence",
        limit=3,
        query_variants=("畢宿",),
        passage_loader=loader,
        strict_exact_passages=True,
    )

    passage_text = "石氏曰畢宿主兵。"
    passage_hash = "sha256:" + hashlib.sha256(passage_text.encode("utf-8")).hexdigest()
    assert loader.calls == [relative_path]
    assert stats["files_scanned"] == 1
    assert len(hits) == 1
    assert hits[0]["page_marker"] == "KR3g0018_WYG_031-17a"
    assert hits[0]["paragraph_index"] == 1
    assert hits[0]["heading_path"] == ["唐開元占經"]
    assert hits[0]["anchor_text"] == passage_text
    assert hits[0]["raw_content_hash"] == passage_hash
    assert hits[0]["normalized_content_hash"] == passage_hash


def test_strict_scanner_propagates_loader_integrity_error(tmp_path: Path):
    class BrokenLoader:
        def relative_paths(self):
            return ("古籍/唐開元占經/分卷/KR3g0018_031.md",)

        def load(self, *_args, **_kwargs):
            raise ReadOnlyAdapterError(ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED)

    with pytest.raises(ReadOnlyAdapterError) as exc_info:
        scan_primary_files(
            SimpleNamespace(
                kb_sources_root=tmp_path,
                kb_enable_obsidian_source=False,
                kb_obsidian_root=tmp_path / "unused",
            ),
            "畢宿",
            book_id="kaiyuan_zhanjing",
            mode="evidence",
            limit=3,
            query_variants=("畢宿",),
            passage_loader=BrokenLoader(),
            strict_exact_passages=True,
        )
    assert exc_info.value.code is ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED


def test_strict_scanner_attempts_manifest_path_even_if_restored_before_postflight(
    tmp_path: Path,
):
    relative_path = "古籍/唐開元占經/分卷/KR3g0018_031.md"
    source = tmp_path / relative_path
    source.parent.mkdir(parents=True)
    raw = (
        "# 唐開元占經\n<pb:KR3g0018_WYG_031-17a>\n石氏曰畢宿主兵。\n"
    ).encode("utf-8")
    source.write_bytes(raw)
    files = [
        {
            "relative_path": relative_path,
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    ]
    tree_sha256 = hashlib.sha256(
        json.dumps(
            files,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    snapshot = LocalKBSourceSnapshotV1.model_validate(
        {
            "schema_version": "local-kb-source-snapshot/v1",
            "snapshot_id": "snapshot:scanner-removal",
            "corpus_version": "20260101T000000Z",
            "collection": "local_kb_kaiyuan_v2",
            "kb_book_id": "kaiyuan_zhanjing",
            "files": files,
            "tree_sha256": tree_sha256,
        }
    )

    with LocalKBSourceAccessor.open(kb_root=tmp_path, snapshot=snapshot) as accessor:
        accessor.assert_bound(
            kb_root=tmp_path,
            snapshot=snapshot,
            snapshot_sha256=canonical_contract_sha256(snapshot),
        )

        class RemovingLoader:
            def relative_paths(self):
                return accessor.relative_paths()

            def load(self, candidate, **kwargs):
                backup = source.with_suffix(".held")
                source.rename(backup)
                try:
                    return accessor.load(candidate, **kwargs)
                finally:
                    backup.rename(source)

        with pytest.raises(ReadOnlyAdapterError) as exc_info:
            scan_primary_files(
                SimpleNamespace(
                    kb_sources_root=tmp_path,
                    kb_enable_obsidian_source=False,
                    kb_obsidian_root=tmp_path / "unused",
                ),
                "畢宿",
                book_id="kaiyuan_zhanjing",
                mode="evidence",
                limit=3,
                query_variants=("畢宿",),
                passage_loader=RemovingLoader(),
                strict_exact_passages=True,
            )
        assert exc_info.value.code is ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED
        accessor.assert_unchanged()
