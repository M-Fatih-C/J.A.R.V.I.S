"""WebSocket /ws endpoint testleri (fake orchestrator ile, model gerekmez)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from jarvis.api.dependencies import get_orchestrator
from jarvis.api.main import app
from jarvis.core import Lane
from jarvis.core.orchestrator import ChatResult


class FakeOrchestrator:
    async def handle(self, message: str, session_id: str = "default") -> ChatResult:
        return ChatResult(
            content=f"echo: {message}",
            model="fake",
            lane=Lane.FAST,
            reason="test",
            latency_ms=1.0,
        )


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_orchestrator] = lambda: FakeOrchestrator()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_orchestrator, None)


def test_ws_chat_flow(client: TestClient) -> None:
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"message": "merhaba", "session_id": "ui"})
        assert ws.receive_json() == {"type": "status", "state": "thinking"}
        response = ws.receive_json()
        assert response["type"] == "response"
        assert response["content"] == "echo: merhaba"
        assert response["lane"] == "fast"
        assert response["model"] == "fake"
        assert ws.receive_json() == {"type": "status", "state": "idle"}


def test_ws_empty_message(client: TestClient) -> None:
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"message": "   "})
        error = ws.receive_json()
        assert error["type"] == "error"


def test_ws_multiple_messages(client: TestClient) -> None:
    with client.websocket_connect("/ws") as ws:
        for msg in ("bir", "iki"):
            ws.send_json({"message": msg})
            assert ws.receive_json()["state"] == "thinking"
            assert ws.receive_json()["content"] == f"echo: {msg}"
            assert ws.receive_json()["state"] == "idle"
