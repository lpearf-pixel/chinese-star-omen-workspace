from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "kb-contracts" / "python"
sys.path.insert(0, str(CONTRACTS))
from kb_contracts import sha256_text  # noqa: E402


def allowed_source(path: Path) -> bool:
    normalized = str(path).replace("\\", "/")
    if "/incoming/downstream_candidates/" in normalized:
        return False
    if "/data/generated/" in normalized and path.suffix == ".md":
        text = path.read_text(encoding="utf-8", errors="ignore")
        return "source_namespace: official" in text or "review_status: approved" in text
    return "/data/sources/" in normalized or "/data/generated/" in normalized


def write_manifest(collection: str, out: Path) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    created_at = now.isoformat().replace("+00:00", "Z")
    corpus_version = now.strftime("%Y-%m-%dT%H%M%SZ")
    ingest_run_id = now.strftime("ingest_%Y%m%d_%H%M%S")
    files = []
    for root in [Path("data/sources"), Path("data/generated")]:
        if root.exists():
            for path in sorted(root.rglob("*")):
                if path.is_file() and allowed_source(path):
                    files.append(f"{path}:{sha256_text(path.read_text(encoding='utf-8', errors='ignore'))}")
    manifest = {
        "schema_version": "corpus-manifest/v1",
        "corpus_version": corpus_version,
        "ingest_run_id": ingest_run_id,
        "source_manifest_hash": sha256_text("\n".join(files)),
        "collection": collection,
        "created_at": created_at,
        "source_roots": ["data/sources", "data/generated"],
        "excluded_roots": ["incoming/downstream_candidates"],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the upstream corpus-manifest/v1 without scanning incoming candidate inboxes.")
    parser.add_argument("--collection", default="star_omen_kb")
    parser.add_argument("--out", type=Path, default=Path("data/corpus_manifest.json"))
    args = parser.parse_args()
    print(json.dumps(write_manifest(args.collection, args.out), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
