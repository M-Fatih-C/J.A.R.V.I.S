"""JarvisClient SDK testleri — httpx MockTransport ile (ağ yok)."""

from __future__ import annotations

import httpx
import pytest

from jarvis.client import JarvisClient


def _client(handler, **kwargs) -> JarvisClient:
    return JarvisClient("http://test", transport=httpx.MockTransport(handler), **kwargs)


def test_authenticate_stores_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/auth/token"
        return httpx.Response(200, json={"access_token": "tok123", "token_type": "bearer"})

    client = _client(handler, device_key="k")
    assert client.authenticate() == "tok123"
    assert client.token == "tok123"


def test_authenticate_without_key_raises() -> None:
    client = _client(lambda r: httpx.Response(200, json={}))
    with pytest.raises(RuntimeError, match="device_key"):
        client.authenticate()


def test_chat_auto_authenticates_and_sends_bearer() -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/token":
            return httpx.Response(200, json={"access_token": "tok", "token_type": "bearer"})
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"content": "merhaba efendim", "lane": "fast"})

    client = _client(handler, device_key="k")
    result = client.chat("selam")
    assert result["content"] == "merhaba efendim"
    assert seen["auth"] == "Bearer tok"


def test_chat_with_preset_token_skips_auth() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, json={"content": "ok"})

    client = _client(handler, token="preset")
    client.chat("hi")
    assert "/auth/token" not in calls  # mevcut token ile auth atlanır


def test_health() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok", "ollama": True})

    assert _client(handler).health()["status"] == "ok"
