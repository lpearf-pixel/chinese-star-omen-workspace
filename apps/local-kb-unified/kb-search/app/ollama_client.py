"""HTTP calls to Ollama for embedding and chat generation."""

from __future__ import annotations

import requests

from . import config


def embed_text(text: str) -> list[float]:
    url = f"{config.OLLAMA_BASE_URL}/api/embeddings"
    response = requests.post(
        url,
        json={"model": config.EMBED_MODEL, "prompt": text},
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    vector = data.get("embedding")
    if not vector:
        raise RuntimeError(f"Ollama embeddings returned no vector: {data}")
    return vector


def chat_completion(system: str, user: str) -> str:
    url = f"{config.OLLAMA_BASE_URL}/api/chat"
    response = requests.post(
        url,
        json={
            "model": config.CHAT_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        },
        timeout=600,
    )
    response.raise_for_status()
    data = response.json()
    message = data.get("message") or {}
    content = message.get("content")
    if not content:
        raise RuntimeError(f"Ollama chat returned no content: {data}")
    return str(content).strip()
