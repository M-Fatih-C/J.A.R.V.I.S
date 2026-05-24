"""OllamaClient için mock'lu birim testler (gerçek sunucu gerektirmez)."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from jarvis.models import ChatMessage, ChatResponse, OllamaClient
from jarvis.models import ollama_client as oc


class FakeResponse:
    """httpx.Response yerine geçen minimal sahte yanıt."""

    def __init__(self, payload: dict[str, Any], status: int = 200) -> None:
        self._payload = payload
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("hata", request=None, response=None)  # type: ignore[arg-type]

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeStream:
    """client.stream(...) için async context manager."""

    def __init__(self, lines: list[str], status: int = 200) -> None:
        self._lines = lines
        self.status_code = status

    async def __aenter__(self) -> FakeStream:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("hata", request=None, response=None)  # type: ignore[arg-type]

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class FakeAsyncClient:
    """httpx.AsyncClient yerine geçen, kaydedilmiş yanıtları döndüren sahte client."""

    post_response: dict[str, Any] | None = None
    get_response: dict[str, Any] | None = None
    stream_lines: list[str] | None = None
    get_should_raise: bool = False

    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    async def post(self, url: str, json: dict[str, Any] | None = None) -> FakeResponse:
        assert FakeAsyncClient.post_response is not None
        return FakeResponse(FakeAsyncClient.post_response)

    async def get(self, url: str) -> FakeResponse:
        if FakeAsyncClient.get_should_raise:
            raise httpx.ConnectError("bağlantı yok")
        assert FakeAsyncClient.get_response is not None
        return FakeResponse(FakeAsyncClient.get_response)

    def stream(self, method: str, url: str, json: dict[str, Any] | None = None) -> FakeStream:
        assert FakeAsyncClient.stream_lines is not None
        return FakeStream(FakeAsyncClient.stream_lines)


@pytest.fixture(autouse=True)
def patch_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    """Her testte modülün httpx.AsyncClient'ını sahte ile değiştirir."""
    FakeAsyncClient.post_response = None
    FakeAsyncClient.get_response = None
    FakeAsyncClient.stream_lines = None
    FakeAsyncClient.get_should_raise = False
    monkeypatch.setattr(oc.httpx, "AsyncClient", FakeAsyncClient)


async def test_chat_returns_chat_response() -> None:
    FakeAsyncClient.post_response = {
        "model": "qwen2.5:14b",
        "message": {"role": "assistant", "content": "İyi günler efendim."},
        "eval_count": 7,
        "done": True,
    }
    client = OllamaClient()
    resp = await client.chat([ChatMessage(role="user", content="Merhaba")])

    assert isinstance(resp, ChatResponse)
    assert resp.content == "İyi günler efendim."
    assert resp.model == "qwen2.5:14b"
    assert resp.tokens == 7
    assert resp.latency_ms >= 0


async def test_chat_uses_override_model() -> None:
    FakeAsyncClient.post_response = {
        "message": {"content": "ok"},
        "done": True,
    }
    client = OllamaClient(default_model="qwen2.5:14b")
    resp = await client.chat([ChatMessage(role="user", content="selam")], model="qwen2.5:7b")
    assert resp.model == "qwen2.5:7b"


async def test_chat_stream_yields_pieces() -> None:
    chunks = [
        {"message": {"content": "Mer"}, "done": False},
        {"message": {"content": "haba"}, "done": False},
        {"message": {"content": ""}, "done": True},
    ]
    FakeAsyncClient.stream_lines = [json.dumps(c) for c in chunks]
    client = OllamaClient()

    pieces = [p async for p in client.chat_stream([ChatMessage(role="user", content="hi")])]
    assert pieces == ["Mer", "haba"]


async def test_chat_with_stream_true_collects_full_text() -> None:
    chunks = [
        {"message": {"content": "A"}, "done": False},
        {"message": {"content": "B"}, "done": True},
    ]
    FakeAsyncClient.stream_lines = [json.dumps(c) for c in chunks]
    client = OllamaClient()

    resp = await client.chat([ChatMessage(role="user", content="hi")], stream=True)
    assert resp.content == "AB"
    assert resp.tokens is None


async def test_embed_single_text() -> None:
    FakeAsyncClient.post_response = {"embeddings": [[0.1, 0.2, 0.3]]}
    client = OllamaClient()
    vectors = await client.embed("merhaba")
    assert vectors == [[0.1, 0.2, 0.3]]


async def test_embed_multiple_texts() -> None:
    FakeAsyncClient.post_response = {"embeddings": [[0.1], [0.2]]}
    client = OllamaClient()
    vectors = await client.embed(["a", "b"])
    assert len(vectors) == 2


def test_embed_model_default() -> None:
    client = OllamaClient()
    assert client.embed_model == "nomic-embed-text"


async def test_list_models() -> None:
    FakeAsyncClient.get_response = {
        "models": [{"name": "qwen2.5:14b"}, {"name": "nomic-embed-text"}]
    }
    client = OllamaClient()
    models = await client.list_models()
    assert models == ["qwen2.5:14b", "nomic-embed-text"]


async def test_health_check_ok() -> None:
    FakeAsyncClient.get_response = {"models": []}
    client = OllamaClient()
    assert await client.health_check() is True


async def test_health_check_failure_returns_false() -> None:
    FakeAsyncClient.get_should_raise = True
    client = OllamaClient()
    assert await client.health_check() is False


def test_base_url_trailing_slash_stripped() -> None:
    client = OllamaClient(base_url="http://localhost:11434/")
    assert client.base_url == "http://localhost:11434"
