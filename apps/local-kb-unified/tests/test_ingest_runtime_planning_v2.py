from __future__ import annotations

import sys
from pathlib import Path

INDEX_JOBS = Path(__file__).resolve().parents[1] / "index-jobs"
sys.path.insert(0, str(INDEX_JOBS))

from ingest import build_payload, scroll_existing_managed  # noqa: E402


class _Record:
    def __init__(self, point_id: str, payload: dict):
        self.id = point_id
        self.payload = payload


class _ScrollClient:
    def __init__(self):
        self.calls = 0

    def scroll(self, **kwargs):
        self.calls += 1
        return (
            [
                _Record(
                    "managed",
                    {
                        "managed_by": "local-kb-unified/v2",
                        "content_hash": "sha256:a",
                    },
                ),
                _Record(
                    "legacy",
                    {"managed_by": "legacy", "content_hash": "sha256:b"},
                ),
            ],
            None,
        )


def test_scroll_existing_managed_ignores_legacy_points():
    client = _ScrollClient()
    existing = scroll_existing_managed(client, "local_kb_kaiyuan_v2")
    assert existing == {
        "managed": {
            "managed_by": "local-kb-unified/v2",
            "content_hash": "sha256:a",
        }
    }
    assert client.calls == 1


def test_build_payload_preserves_primary_passage_provenance():
    item = {
        "doc_id": "doc",
        "chunk_id": "chunk",
        "source_type": "docs",
        "path": "/corpus/KR3g0018_031.md",
        "title": "KR3g0018_031.md",
        "chunk_text": "石氏曰熒惑守心。",
        "chunk_index": 0,
        "mtime": 1,
        "content_hash": "sha256:raw",
        "raw_content_hash": "sha256:raw",
        "normalized_content_hash": "sha256:normalized",
        "normalized_text": "石氏曰荧惑守心。",
        "managed_by": "local-kb-unified/v2",
        "collection_schema": "passage-v2",
        "ingest_source": "default",
        "source_root_label": "primary",
        "relative_path": "古籍/唐開元占經/分卷/KR3g0018_031.md",
        "kb_book_id": "kaiyuan_zhanjing",
        "book_title": "唐開元占經",
        "card_type": "fenjuan",
        "evidence_level": "primary",
        "final_citable": True,
        "query_mode_hint": "evidence",
        "source_locator": "KR3g0018_031",
        "source_volume": "卷31",
        "page_marker": "KR3g0018_WYG_031-17a",
        "heading_path": ["熒惑占二", "熒惑犯心五"],
        "paragraph_index": 0,
        "raw_start": 10,
        "raw_end": 20,
        "source_refs": ["fulltext.md"],
    }

    payload = build_payload(item)

    assert payload["managed_by"] == "local-kb-unified/v2"
    assert payload["collection_schema"] == "passage-v2"
    assert payload["kb_book_id"] == "kaiyuan_zhanjing"
    assert payload["source_locator"] == "KR3g0018_031"
    assert payload["page_marker"] == "KR3g0018_WYG_031-17a"
    assert payload["heading_path"] == ["熒惑占二", "熒惑犯心五"]
    assert payload["raw_start"] == 10
    assert payload["raw_end"] == 20
    assert payload["source_refs"] == ["fulltext.md"]
    assert "book_id" not in payload
