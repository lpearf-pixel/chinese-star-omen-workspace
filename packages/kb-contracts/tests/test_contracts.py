from pathlib import Path

from kb_contracts import merge_candidate_item, new_candidate_manifest, normalize_term, save_candidate_manifest, load_candidate_manifest, sha256_text, stable_candidate_id


def test_normalize_and_stable_id():
    assert normalize_term("熒惑 守心") == "yinghuo_shouxin"
    assert stable_candidate_id("kaiyuan_zhanjing", "荧惑守心", "KR3g0018_031", 12345) == "kaiyuan_zhanjing:yinghuo_shouxin:KR3g0018_031:12345"


def test_sha256_text_stable():
    assert sha256_text("abc") == sha256_text("abc")
    assert sha256_text("abc").startswith("sha256:")


def test_manifest_merge_dedupes(tmp_path: Path):
    manifest = new_candidate_manifest("kaiyuan_zhanjing")
    item = {"id": "a", "term": "荧惑守心"}
    merge_candidate_item(manifest, item)
    merge_candidate_item(manifest, {**item, "sync_status": "pending"})
    assert len(manifest["items"]) == 1
    path = tmp_path / "candidate_manifest.json"
    save_candidate_manifest(path, manifest)
    assert load_candidate_manifest(path)["items"][0]["id"] == "a"
