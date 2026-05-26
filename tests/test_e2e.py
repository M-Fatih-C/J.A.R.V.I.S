"""Uçtan uca testler — /chat'i Orchestrator üzerinden gerçek modellerle dener.

- Fast Lane (MLX) her zaman çalışır (mlx-lm kurulu); kısa mesaj fast'a gider.
- Deep Think (Ollama/Qwen) yalnızca model yüklüyse test edilir, aksi halde skip.

Gecikme üzerine katı sınır yoktur (yerel LLM'ler donanıma göre değişir);
testler doğru yönlendirme ve boş olmayan yanıt üzerine odaklanır.
"""

from __future__ import annotations

import os

import httpx
import pytest
from httpx import ASGITransport

from jarvis.api.dependencies import get_ollama_client
from jarvis.api.main import app
from jarvis.config import settings


@pytest.fixture
async def client() -> httpx.AsyncClient:
    """Uygulamaya doğrudan (ağ olmadan) bağlanan async test client'ı."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _deep_model_ready() -> bool:
    """Ollama erişilebilir VE Deep Think modeli yüklü mü?"""
    ollama = get_ollama_client()
    if not await ollama.health_check():
        return False
    try:
        models = await ollama.list_models()
    except Exception:  # noqa: BLE001
        return False
    target = settings.ollama_default_model.split(":")[0]
    return any(m.split(":")[0] == target for m in models)


async def test_health_endpoint(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert isinstance(body["ollama"], bool)


@pytest.mark.skipif(
    "JARVIS_E2E" not in os.environ,
    reason="Gerçek model e2e testi atlandı (JARVIS_E2E=1 ile etkinleşir).",
)
async def test_chat_fast_lane(client: httpx.AsyncClient) -> None:
    """Kısa mesaj Fast Lane'e (MLX) gider ve boş olmayan yanıt döner."""
    resp = await client.post("/chat", json={"message": "Merhaba"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["lane"] == "fast"
    assert body["content"].strip(), "Yanıt boş gelmemeli"


@pytest.mark.skipif(
    "JARVIS_E2E" not in os.environ,
    reason="Gerçek model e2e testi atlandı (JARVIS_E2E=1 ile etkinleşir).",
)
async def test_chat_deep_lane(client: httpx.AsyncClient) -> None:
    """Derin-anahtar kelimeli mesaj Deep Think'e (Ollama) gider."""
    if not await _deep_model_ready():
        pytest.skip(
            f"Ollama'da '{settings.ollama_default_model}' modeli yok; "
            "deep lane e2e testi atlandı."
        )
    resp = await client.post("/chat", json={"message": "Bu konuyu kısaca açıkla: güneş sistemi"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["lane"] == "deep"
    assert body["model"].split(":")[0] == settings.ollama_default_model.split(":")[0]
    assert body["content"].strip(), "Yanıt boş gelmemeli"
