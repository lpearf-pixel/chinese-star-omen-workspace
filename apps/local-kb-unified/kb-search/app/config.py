"""Load KB Search settings from environment or a local `.env` file."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_pkg_root = Path(__file__).resolve().parent.parent
_repo_root = _pkg_root.parent
for _env_path in (_repo_root / ".env", _pkg_root / ".env"):
    if _env_path.is_file():
        load_dotenv(_env_path)
        break

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "127.0.0.1")
OLLAMA_PORT = int(os.environ.get("OLLAMA_PORT", "11434"))
QDRANT_HOST = os.environ.get("QDRANT_HOST", "127.0.0.1")
QDRANT_HTTP_PORT = int(os.environ.get("QDRANT_HTTP_PORT", "6333"))

CHAT_MODEL = os.environ.get("CHAT_MODEL", "qwen2.5-coder:7b-instruct")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")

KB_SEARCH_API_KEY = os.environ.get("KB_SEARCH_API_KEY", "").strip()
if not KB_SEARCH_API_KEY:
    raise RuntimeError("KB_SEARCH_API_KEY must be non-empty")
KB_SEARCH_DEFAULT_COLLECTION = os.environ.get(
    "KB_SEARCH_DEFAULT_COLLECTION", "local_kb_kaiyuan_v2"
)

_manifest_default = _repo_root / "data" / "corpus_manifest.json"
KB_CORPUS_MANIFEST_PATH = Path(
    os.environ.get("KB_CORPUS_MANIFEST_PATH", str(_manifest_default))
).expanduser()


def _env_truthy(key: str, default: str = "1") -> bool:
    return os.environ.get(key, default).strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


KB_QUERY_STELLAR_NORMALIZE = _env_truthy("KB_QUERY_STELLAR_NORMALIZE", "1")
KB_OPENCC_CONFIG = os.environ.get("KB_OPENCC_CONFIG", "s2t").strip()
KB_QUERY_DUAL_SCRIPT = _env_truthy("KB_QUERY_DUAL_SCRIPT", "0")
KB_LITERAL_POOL_FACTOR = max(
    2, min(40, int(os.environ.get("KB_LITERAL_POOL_FACTOR", "12")))
)
KB_LITERAL_POOL_CAP = max(
    20, min(200, int(os.environ.get("KB_LITERAL_POOL_CAP", "120")))
)

OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_HTTP_PORT}"
