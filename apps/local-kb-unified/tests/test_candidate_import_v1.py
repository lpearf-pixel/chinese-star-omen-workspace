from pathlib import Path

import yaml

from scripts.import_candidate_cards import promote_mode, validate_mode
from scripts.corpus_manifest import write_manifest


def _card(tmp_path: Path, status="pending") -> Path:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    meta = {
        "schema_version": "candidate-card/v1",
        "kb_book_id": "kaiyuan_zhanjing",
        "book_title": "唐開元占經",
        "card_type": "extract_card",
        "evidence_level": "candidate",
        "source_namespace": "downstream_generated",
        "generated_by": "codex_ready_filesystem_fallback",
        "generated_status": "candidate",
        "review_status": status,
        "sync_status": "pending",
        "term": "荧惑守心",
        "aliases": ["熒惑守心"],
        "source_file": "古籍/唐開元占經/分卷/KR3g0018_031.md",
        "source_locator": "KR3g0018_031",
        "source_volume": "卷31",
        "page_marker": "KR3g0018_WYG_031-1a",
        "heading_path": ["熒惑占二"],
        "paragraph_index": 3,
        "match_type": "exact_phrase",
        "match_offset": 12345,
        "anchor_text": "……熒惑守心……",
        "content_hash": "sha256:" + "a" * 64,
        "base_corpus_version": "unknown",
        "base_ingest_run_id": "unknown",
    }
    (inbox / "yinghuo_shouxin.KR3g0018_031.md").write_text("---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n# 荧惑守心\n", encoding="utf-8")
    (inbox / "candidate_manifest.json").write_text('{"schema_version":"candidate-manifest/v1","source_project":"Codex-ready-chinese-star-omen-project","target_upstream":"Local-KB-Unified","book_id":"kaiyuan_zhanjing","base_corpus_version":"unknown","base_ingest_run_id":"unknown","current_upstream_corpus_version":null,"last_synced_at":null,"items":[{"id":"kaiyuan_zhanjing:yinghuo_shouxin:KR3g0018_031:12345","file":"yinghuo_shouxin.KR3g0018_031.md","term":"荧惑守心","source_locator":"KR3g0018_031","source_volume":"卷31","match_offset":12345,"content_hash":"sha256:' + 'a'*64 + '","anchor_text":"……熒惑守心……","review_status":"' + status + '","sync_status":"pending"}]}', encoding="utf-8")
    return inbox


def test_validate_and_promote_approved(monkeypatch, tmp_path):
    inbox = _card(tmp_path, "approved")
    monkeypatch.chdir(tmp_path)
    assert validate_mode(inbox, "kaiyuan_zhanjing") == 0
    assert promote_mode(inbox, "kaiyuan_zhanjing") == 0
    promoted = tmp_path / "data/generated/extract_cards/kaiyuan_zhanjing/yinghuo_shouxin.KR3g0018_031.md"
    assert promoted.exists()
    fm = yaml.safe_load(promoted.read_text(encoding="utf-8").split("---", 2)[1])
    assert fm["evidence_level"] == "primary"
    assert fm["source_namespace"] == "official"


def test_pending_not_promoted(monkeypatch, tmp_path):
    inbox = _card(tmp_path, "pending")
    monkeypatch.chdir(tmp_path)
    assert promote_mode(inbox, "kaiyuan_zhanjing") == 0
    assert not (tmp_path / "data/generated/extract_cards/kaiyuan_zhanjing/yinghuo_shouxin.KR3g0018_031.md").exists()


def test_corpus_manifest_excludes_incoming(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "incoming/downstream_candidates/codex-ready").mkdir(parents=True)
    (tmp_path / "incoming/downstream_candidates/codex-ready/bad.md").write_text("pending", encoding="utf-8")
    manifest = write_manifest("star_omen_kb", tmp_path / "data/corpus_manifest.json")
    assert manifest["schema_version"] == "corpus-manifest/v1"
    assert "incoming/downstream_candidates" in manifest["excluded_roots"]
