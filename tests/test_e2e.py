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

from jarvis.api.auth import get_current_principal
from jarvis.api.dependencies import get_agent, get_ollama_client
from jarvis.api.main import app
from jarvis.config import settings


@pytest.fixture
async def client() -> httpx.AsyncClient:
    """Uygulamaya doğrudan (ağ olmadan) bağlanan async test client'ı (auth bypass)."""
    app.dependency_overrides[get_current_principal] = lambda: "test"
    transport = ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_current_principal, None)


class _FakeAgent:
    """LLM çağırmadan sabit yanıt veren sahte agent (route testi için)."""

    async def run(self, message: str) -> str:
        return f"sahte yanıt: {message}"


async def test_agent_endpoint_wiring(client: httpx.AsyncClient) -> None:
    """/agent endpoint'i agent'ı çağırıp yanıtı döndürür (DI override ile)."""
    app.dependency_overrides[get_agent] = lambda: _FakeAgent()
    try:
        resp = await client.post("/agent", json={"message": "selam"})
    finally:
        app.dependency_overrides.pop(get_agent, None)
    assert resp.status_code == 200, resp.text
    assert resp.json()["content"] == "sahte yanıt: selam"


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


@pytest.mark.skipif(
    "JARVIS_E2E" not in os.environ,
    reason="Gerçek agent e2e testi atlandı (JARVIS_E2E=1 ile etkinleşir).",
)
async def test_agent_endpoint_real(client: httpx.AsyncClient) -> None:
    """/agent gerçek agent ile araç çağırarak yanıt üretir."""
    if not await _deep_model_ready():
        pytest.skip(f"Ollama'da '{settings.ollama_default_model}' modeli yok.")
    resp = await client.post(
        "/agent",
        json={"message": "5 ile 7'yi topla, sonucu run_python ile hesaplayıp söyle."},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["content"].strip(), "Yanıt boş gelmemeli"
