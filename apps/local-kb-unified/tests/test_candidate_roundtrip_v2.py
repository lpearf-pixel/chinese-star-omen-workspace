from __future__ import annotations

import importlib
import json
import os
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

WORKSPACE = Path(__file__).resolve().parents[3]
UPSTREAM = Path(__file__).resolve().parents[1]
INDEX_JOBS = UPSTREAM / "index-jobs"
UPSTREAM_SCRIPTS = UPSTREAM / "scripts"
DOWNSTREAM = WORKSPACE / "apps" / "star-omen"
for path in (INDEX_JOBS, UPSTREAM_SCRIPTS, DOWNSTREAM):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from desired_items import collect_desired_items  # noqa: E402
from import_candidate_cards import promote_mode  # noqa: E402
from incremental import execute_reconciliation, plan_reconciliation  # noqa: E402
from ingest import build_payload  # noqa: E402
from kb_contracts import SyncErrorCode  # noqa: E402
from src.candidate_cards import generate_candidate_cards  # noqa: E402
from src.candidate_sync import sync_candidate_manifests  # noqa: E402
from src.config.settings import reload_settings  # noqa: E402
from src.connectors.evidence_resolver import resolve_evidence  # noqa: E402
from src.connectors.kb_search_retriever import KBSearchError, KBSearchRetriever  # noqa: E402

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_CANDIDATE_ROUNDTRIP") != "1",
    reason="requires ephemeral Qdrant service",
)

PAGE = "KR3g0018_WYG_031-17a"
RAW = "石氏曰熒惑守心，天下兵起。"
BOOK_ID = "kaiyuan_zhanjing"


def _load_main(monkeypatch):
    monkeypatch.setenv("KB_SEARCH_API_KEY", "roundtrip-key")
    monkeypatch.setenv("KB_SEARCH_DEFAULT_COLLECTION", "local_kb_kaiyuan_v2")
    monkeypatch.syspath_prepend(str(UPSTREAM / "kb-search"))
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)
    return importlib.import_module("app.main")


def _approve_candidate(out_dir: Path) -> None:
    card = next(out_dir.glob("*.md"))
    text = card.read_text(encoding="utf-8")
    _empty, raw, body = text.split("---", 2)
    metadata = yaml.safe_load(raw) or {}
    metadata["review_status"] = "approved"
    metadata["sync_status"] = "pending"
    card.write_text(
        "---\n"
        + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False)
        + "---"
        + body,
        encoding="utf-8",
    )

    manifest_path = out_dir / "candidate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["items"][0]["review_status"] = "approved"
    manifest["items"][0]["sync_status"] = "pending"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_candidate_roundtrip_promotes_retrieves_syncs_and_validates_citation(
    monkeypatch,
    tmp_path: Path,
):
    sources = tmp_path / "sources"
    volume = sources / "古籍" / "唐開元占經" / "分卷" / "KR3g0018_031.md"
    volume.parent.mkdir(parents=True)
    volume.write_text(
        "# 唐開元占經 卷31\n\n"
        "　熒惑占二\n"
        "　　　熒惑犯心五\n"
        f"<pb:{PAGE}>\n{RAW}\n",
        encoding="utf-8",
    )

    # The integration test runs from the workspace root, while the downstream
    # application intentionally keeps its config inside apps/star-omen.
    monkeypatch.setenv("APP_CONFIG_PATH", str(DOWNSTREAM / "config" / "config.yaml"))
    monkeypatch.setenv("KB_SOURCES_ROOT", str(sources))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "false")
    reload_settings()
    monkeypatch.setattr(
        KBSearchRetriever,
        "get_upstream_meta",
        lambda self: {
            "meta_status": "ok",
            "corpus_version": "roundtrip-v1",
            "ingest_run_id": "roundtrip-run",
            "source_manifest_hash": "sha256:source",
            "collection": "local_kb_kaiyuan_v2",
        },
    )

    candidate_root = tmp_path / "downstream_candidates"
    candidate_out = candidate_root / "extract_cards" / BOOK_ID
    generated = generate_candidate_cards("荧惑守心", BOOK_ID, candidate_out)
    assert len(generated["generated"]) == 1
    _approve_candidate(candidate_out)

    upstream_workdir = tmp_path / "upstream"
    upstream_workdir.mkdir()
    monkeypatch.chdir(upstream_workdir)
    assert promote_mode(candidate_out, BOOK_ID) == 0
    promoted_root = upstream_workdir / "data" / "generated"
    promoted_cards = list(promoted_root.rglob("*.md"))
    assert len(promoted_cards) == 1
    promoted_meta = yaml.safe_load(
        promoted_cards[0].read_text(encoding="utf-8").split("---", 2)[1]
    )
    assert promoted_meta["source_namespace"] == "official"
    assert promoted_meta["evidence_level"] == "primary"

    desired = collect_desired_items(
        sources,
        generated_root=promoted_root,
        obsidian_root=None,
        chunk_size=700,
        overlap=120,
    )
    assert any(item.get("card_type") == "fenjuan" for item in desired)
    extract_items = [item for item in desired if item.get("card_type") == "extract_card"]
    # A single reviewed Markdown card may produce multiple heading-level
    # retrieval records. They must all carry the same official approval and
    # candidate provenance; the roundtrip invariant is the card/hash, not one
    # Qdrant point per Markdown file.
    assert extract_items
    assert all(item["review_status"] == "approved" for item in extract_items)
    assert all(item["source_namespace"] == "official" for item in extract_items)

    client = QdrantClient(
        url=os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"),
        timeout=30,
    )
    collection = "candidate_roundtrip_" + uuid.uuid4().hex
    client.create_collection(
        collection_name=collection,
        vectors_config=qm.VectorParams(size=2, distance=qm.Distance.COSINE),
    )

    def upsert_batch(records):
        client.upsert(
            collection_name=collection,
            wait=True,
            points=[
                qm.PointStruct(
                    id=record["point_id"],
                    vector=record["vector"],
                    payload=build_payload(record["item"]),
                )
                for record in records
            ],
        )

    try:
        plan = plan_reconciliation(desired, {}, mode="incremental")
        result = execute_reconciliation(
            plan,
            embed_item=lambda item: [1.0, 0.0],
            upsert_batch=upsert_batch,
            delete_points=lambda ids: None,
            batch_size=16,
        )
        assert result["upserted"] == len(desired)

        main = _load_main(monkeypatch)
        monkeypatch.setattr(main, "_qdrant_client", lambda: client)
        monkeypatch.setattr(main.ollama_client, "embed_text", lambda text: [1.0, 0.0])
        monkeypatch.setattr(main, "iter_embedding_query_strings", lambda text: [text])
        response = main.retrieve(
            main.RetrieveRequest(
                query="荧惑守心",
                collection=collection,
                query_mode="evidence",
                retrieval_stage="structured_recall",
                card_types=["extract_card"],
                filters={"kb_book_id": BOOK_ID},
                literal_first=True,
            )
        )
        expected_hash = json.loads(
            (candidate_out / "candidate_manifest.json").read_text(encoding="utf-8")
        )["items"][0]["content_hash"]
        assert response.retrieved_count >= 1
        assert all(hit.card_type == "extract_card" for hit in response.hits)
        assert any(hit.content_hash == expected_hash for hit in response.hits)

        class RoundtripRetriever:
            settings = SimpleNamespace(kb_sources_root=str(sources))

            def get_upstream_meta(self):
                return {
                    "meta_status": "ok",
                    "corpus_version": "roundtrip-v2",
                    "ingest_run_id": "roundtrip-ingest",
                    "source_manifest_hash": "sha256:roundtrip",
                    "collection": collection,
                }

            def retrieve(self, query, **kwargs):
                request = main.RetrieveRequest(
                    query=query,
                    top_k=kwargs.get("top_k", 20),
                    collection=collection,
                    filters=kwargs.get("filters"),
                    query_mode=kwargs.get("query_mode"),
                    retrieval_stage=kwargs.get(
                        "retrieval_stage",
                        "structured_recall",
                    ),
                    card_types=kwargs.get("card_types"),
                    literal_first=kwargs.get("literal_first", True),
                )
                return main.retrieve(request).model_dump()

        sync_report = sync_candidate_manifests(
            BOOK_ID,
            candidate_root,
            retriever=RoundtripRetriever(),
            now="2026-07-17T20:00:00Z",
        )
        assert sync_report["run_status"] == "ok"
        assert sync_report["updated"]["merged"] == 1
        manifest_path = candidate_out / "candidate_manifest.json"
        assert json.loads(manifest_path.read_text(encoding="utf-8"))["items"][0][
            "sync_status"
        ] == "merged"

        before_error = manifest_path.read_bytes()

        class BrokenRetriever(RoundtripRetriever):
            def retrieve(self, query, **kwargs):
                raise KBSearchError(
                    "temporary timeout",
                    code=SyncErrorCode.TIMEOUT,
                    status_code=408,
                )

        error_report = sync_candidate_manifests(
            BOOK_ID,
            candidate_root,
            retriever=BrokenRetriever(),
        )
        assert error_report["run_status"] == "error"
        assert error_report["error"]["code"] == "timeout"
        assert manifest_path.read_bytes() == before_error

        primary_item = next(
            item for item in desired if item.get("card_type") == "fenjuan"
        )
        resolved = resolve_evidence(
            {
                "kb_book_id": BOOK_ID,
                "card_type": "fenjuan",
                "relative_path": "古籍/唐開元占經/分卷/KR3g0018_031.md",
                "source_locator": primary_item["source_locator"],
                "page_marker": primary_item["page_marker"],
                "heading_path": primary_item["heading_path"],
                "paragraph_index": primary_item["paragraph_index"],
                "anchor_text": primary_item["chunk_text"],
                "content_hash": primary_item["raw_content_hash"],
            },
            sources,
        )
        assert resolved["status"] == "citable"
        assert resolved["trace"]["checks"]["hash"] is True
    finally:
        client.delete_collection(collection)
