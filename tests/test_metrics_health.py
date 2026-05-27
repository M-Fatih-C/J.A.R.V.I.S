"""/metrics, zenginleştirilmiş /health ve request-id middleware testleri."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from jarvis.api.dependencies import (
    get_mlx_client,
    get_ollama_client,
    get_short_term_memory,
)
from jarvis.api.main import app


class _FakeOllama:
    async def health_check(self) -> bool:
        return True


class _FakeMLX:
    async def health_check(self) -> bool:
        return True


class _FakeRedisMem:
    async def ping(self) -> bool:
        return False


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_ollama_client] = lambda: _FakeOllama()
    app.dependency_overrides[get_mlx_client] = lambda: _FakeMLX()
    app.dependency_overrides[get_short_term_memory] = lambda: _FakeRedisMem()
    try:
        yield TestClient(app)
    finally:
        for dep in (get_ollama_client, get_mlx_client, get_short_term_memory):
            app.dependency_overrides.pop(dep, None)


def test_health_reports_subsystems(client: TestClient) -> None:
    body = client.get("/health").json()
    assert body == {"status": "ok", "ollama": True, "mlx": True, "redis": False}


def test_request_id_header(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.headers.get("X-Request-ID")


def test_request_id_is_echoed(client: TestClient) -> None:
    resp = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert resp.headers["X-Request-ID"] == "abc123"


def test_metrics_endpoint(client: TestClient) -> None:
    client.get("/health")  # en az bir istek kaydı üret
    resp = client.get("/metrics")
    assert resp.status_code == 200
    text = resp.text
    assert "jarvis_requests_total" in text
    assert "jarvis_chat_total" in text
    assert "jarvis_request_duration_seconds" in text
