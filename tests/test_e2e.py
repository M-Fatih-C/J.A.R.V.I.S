"""Uçtan uca testler — gerçek Ollama + yüklü model gerektirir.

Varsayılan model erişilebilir değilse /chat testi otomatik atlanır (skip),
böylece model çekilmeden de test paketi yeşil kalır.
"""

from __future__ import annotations

import time

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


async def _default_model_ready() -> bool:
    """Ollama erişilebilir VE varsayılan model yüklü mü?"""
    client = get_ollama_client()
    if not await client.health_check():
        return False
    try:
        models = await client.list_models()
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


async def test_chat_roundtrip(client: httpx.AsyncClient) -> None:
    if not await _default_model_ready():
        pytest.skip(
            f"Ollama'da '{settings.ollama_default_model}' modeli yok; "
            "/chat e2e testi atlandı. (ollama pull ile çekin)"
        )

    start = time.perf_counter()
    resp = await client.post("/chat", json={"message": "Merhaba"})
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["content"].strip(), "Yanıt boş gelmemeli"
    assert elapsed < 5.0, f"Yanıt 5 saniyeyi aştı: {elapsed:.1f}s"
