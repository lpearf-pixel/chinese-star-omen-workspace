from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_real_runtime_layout_is_present():
    required = [
        "docker-compose.yml",
        ".env.example",
        "kb-search/Dockerfile",
        "kb-search/app/main.py",
        "index-jobs/ingest.py",
        "index-jobs/sources/obsidian_adapter.py",
        "scripts/healthcheck.sh",
        "scripts/kb_retrieve_smoke.sh",
        "RUNTIME_BASELINE.json",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    assert missing == []


def test_compose_uses_required_services_and_named_data_volumes():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert {"qdrant", "postgres", "kb-search", "open-webui"} <= set(services)
    assert services["qdrant"]["volumes"] == ["qdrant_data:/qdrant/storage"]
    assert services["postgres"]["volumes"] == ["postgres_data:/var/lib/postgresql/data"]
    assert {"qdrant_data", "postgres_data", "openwebui_data"} <= set(compose["volumes"])


def test_trial_collection_and_non_destructive_ingest_are_defaults():
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "KB_SEARCH_DEFAULT_COLLECTION=local_kb_kaiyuan_v2" in env_example

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    ingest_body = makefile.split("\ningest:\n", 1)[1].split("\n\n", 1)[0]
    assert "--recreate" not in ingest_body
    assert "\ningest-recreate:\n" in makefile


def test_candidate_and_incoming_boundaries_are_preserved():
    assert (ROOT / "scripts/import_candidate_cards.py").is_file()
    manifest_script = (ROOT / "scripts/corpus_manifest.py").read_text(encoding="utf-8")
    assert "incoming/downstream_candidates" in manifest_script


def test_runtime_baseline_records_reviewed_snapshot():
    baseline = json.loads((ROOT / "RUNTIME_BASELINE.json").read_text(encoding="utf-8"))
    assert baseline["source_repository"] == "lpearf-pixel/Local-KB-Unified"
    assert baseline["source_commit"] == "62cb52f314a8424713a605bda2fb6dab3c5bdbb5"
    assert baseline["archive_sha256"] == "1b8d26df4ebbbdeff3a02c6cbf672cfba0ad086bf629b4bcf29439d7a76023de"
    assert baseline["default_collection"] == "local_kb_kaiyuan_v2"


def test_runtime_tree_excludes_machine_local_and_secret_artifacts():
    forbidden_names = {".env", ".DS_Store", "Gemma-4-31B-JANG_4M-CRACK-Q4_K_M.gguf"}
    found = [str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.name in forbidden_names]
    assert found == []
