from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from kb_contracts import SyncErrorCode
from src.candidate_sync import sync_candidate_manifests
from src.connectors.kb_search_retriever import KBSearchError


BOOK_ID = "kaiyuan_zhanjing"


def _fixture(tmp_path: Path, *, item_count: int = 1) -> tuple[Path, Path, Path]:
    sources = tmp_path / "sources"
    source = sources / "古籍" / "唐開元占經" / "分卷" / "KR3g0018_031.md"
    source.parent.mkdir(parents=True)
    source.write_text("# 卷三十一\n\n石氏曰熒惑守心，天下兵起。\n", encoding="utf-8")

    root = tmp_path / "generated_candidates"
    inbox = root / "extract_cards" / BOOK_ID
    inbox.mkdir(parents=True)
    items = []
    for index in range(item_count):
        file_name = f"candidate-{index}.md"
        anchor = "石氏曰熒惑守心，天下兵起。"
        metadata = {
            "schema_version": "candidate-card/v1",
            "kb_book_id": BOOK_ID,
            "card_type": "extract_card",
            "review_status": "pending",
            "sync_status": "pending",
            "term": "荧惑守心",
            "source_file": "古籍/唐開元占經/分卷/KR3g0018_031.md",
            "source_locator": "KR3g0018_031",
            "anchor_text": anchor,
            "content_hash": f"sha256:hash-{index}",
        }
        (inbox / file_name).write_text(
            "---\n"
            + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False)
            + "---\n\n"
            + anchor
            + "\n",
            encoding="utf-8",
        )
        items.append(
            {
                "id": f"candidate-{index}",
                "file": file_name,
                "term": "荧惑守心",
                "source_locator": "KR3g0018_031",
                "content_hash": f"sha256:hash-{index}",
                "anchor_text": anchor,
                "review_status": "pending",
                "sync_status": "pending" if index == 0 else "needs_review",
            }
        )

    manifest = {
        "schema_version": "candidate-manifest/v1",
        "source_project": "downstream",
        "target_upstream": "Local-KB-Unified",
        "book_id": BOOK_ID,
        "base_corpus_version": "base-v1",
        "base_ingest_run_id": "base-run",
        "current_upstream_corpus_version": None,
        "last_synced_at": None,
        "items": items,
    }
    manifest_path = inbox / "candidate_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return root, sources, manifest_path


class FakeRetriever:
    def __init__(self, sources: Path, responses):
        self.settings = SimpleNamespace(kb_sources_root=str(sources))
        self.responses = list(responses)
        self.calls: list[dict] = []

    def get_upstream_meta(self):
        return {
            "meta_status": "ok",
            "corpus_version": "upstream-v2",
            "ingest_run_id": "upstream-run",
            "source_manifest_hash": "sha256:meta",
            "collection": "local_kb_kaiyuan_v2",
        }

    def retrieve(self, query, **kwargs):
        self.calls.append({"query": query, **kwargs})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _hits(*rows: dict) -> dict:
    return {
        "schema_version": "kb-retrieve/v2",
        "retrieval_stage": "structured_recall",
        "card_types": ["extract_card"],
        "hits": list(rows),
        "retrieved_count": len(rows),
    }


def test_successful_sync_classifies_merged_review_pending_and_stale(tmp_path: Path):
    root, sources, manifest_path = _fixture(tmp_path, item_count=4)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for index, item in enumerate(manifest["items"]):
        item["content_hash"] = f"sha256:hash-{index}"
        item["file"] = f"candidate-{index}.md"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Make the fourth local card stale before any upstream query.
    stale_card = manifest_path.parent / "candidate-3.md"
    stale_text = stale_card.read_text(encoding="utf-8")
    stale_card.write_text(stale_text.replace("石氏曰熒惑守心，天下兵起。", "本地锚点已移除。"), encoding="utf-8")

    retriever = FakeRetriever(
        sources,
        [
            _hits({"card_type": "extract_card", "content_hash": "sha256:hash-0", "snippet": "same"}),
            _hits({"card_type": "extract_card", "content_hash": "sha256:different", "snippet": "other"}),
            _hits(),
        ],
    )
    report = sync_candidate_manifests(
        BOOK_ID,
        root,
        retriever=retriever,
        now="2026-07-17T18:00:00Z",
    )

    assert report["schema_version"] == "candidate-sync-report/v2"
    assert report["run_status"] == "ok"
    assert report["error"] is None
    assert report["checked"] == 4
    assert report["updated"] == {
        "merged": 1,
        "needs_review": 1,
        "pending": 1,
        "stale": 1,
    }
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [item["sync_status"] for item in written["items"]] == [
        "merged",
        "needs_review",
        "pending",
        "stale",
    ]
    assert written["current_upstream_corpus_version"] == "upstream-v2"
    assert written["last_synced_at"] == "2026-07-17T18:00:00Z"
    assert all(call["retrieval_stage"] == "structured_recall" for call in retriever.calls)
    assert all(call["card_types"] == ["extract_card"] for call in retriever.calls)
    assert all(call["filters"] == {"kb_book_id": BOOK_ID} for call in retriever.calls)


@pytest.mark.parametrize(
    "code,status_code",
    [
        (SyncErrorCode.AUTHENTICATION_FAILED, 401),
        (SyncErrorCode.TIMEOUT, 408),
        (SyncErrorCode.UPSTREAM_UNAVAILABLE, 503),
        (SyncErrorCode.CONTRACT_ERROR, 422),
        (SyncErrorCode.COLLECTION_NOT_FOUND, 404),
        (SyncErrorCode.INVALID_RESPONSE, 200),
    ],
)
def test_meta_failure_preserves_manifest_bytes(tmp_path: Path, code, status_code):
    root, sources, manifest_path = _fixture(tmp_path)
    before = manifest_path.read_bytes()

    retriever = FakeRetriever(sources, [])
    retriever.get_upstream_meta = lambda: (_ for _ in ()).throw(
        KBSearchError("failed", code=code, status_code=status_code)
    )
    report = sync_candidate_manifests(BOOK_ID, root, retriever=retriever)

    assert report["run_status"] == "error"
    assert report["error"]["code"] == code.value
    assert report["preserved"] == 1
    assert manifest_path.read_bytes() == before


def test_item_failure_after_prior_success_does_not_partially_write(tmp_path: Path):
    root, sources, manifest_path = _fixture(tmp_path, item_count=2)
    before = manifest_path.read_bytes()
    retriever = FakeRetriever(
        sources,
        [
            _hits({"card_type": "extract_card", "content_hash": "sha256:hash-0"}),
            KBSearchError(
                "timeout after first item",
                code=SyncErrorCode.TIMEOUT,
                status_code=408,
            ),
        ],
    )

    report = sync_candidate_manifests(BOOK_ID, root, retriever=retriever)

    assert report["run_status"] == "error"
    assert report["error"]["code"] == "timeout"
    assert report["checked"] == 1
    assert report["preserved"] == 2
    assert manifest_path.read_bytes() == before
