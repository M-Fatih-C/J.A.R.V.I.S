"""MLXClient için birim testler — mlx_lm fonksiyonları mock'lanır (model yüklenmez)."""

from __future__ import annotations

from typing import Any

import mlx_lm
import pytest

from jarvis.models import ChatMessage, ChatResponse, MLXClient


class FakeTokenizer:
    """apply_chat_template + encode sağlayan minimal sahte tokenizer."""

    chat_template = "<template>"

    def apply_chat_template(
        self, dicts: list[dict[str, str]], add_generation_prompt: bool, tokenize: bool
    ) -> str:
        return "PROMPT:" + dicts[-1]["content"]

    def encode(self, text: str) -> list[int]:
        return list(range(len(text.split())))


class _StreamPiece:
    def __init__(self, text: str) -> None:
        self.text = text


@pytest.fixture(autouse=True)
def patch_mlx(monkeypatch: pytest.MonkeyPatch) -> None:
    """mlx_lm.load/generate/stream_generate fonksiyonlarını sahteler."""

    def fake_load(name: str) -> tuple[object, FakeTokenizer]:
        return object(), FakeTokenizer()

    def fake_generate(
        model: Any, tokenizer: Any, prompt: str, max_tokens: int, verbose: bool
    ) -> str:
        return "  İyi günler efendim.  "

    def fake_stream_generate(model: Any, tokenizer: Any, prompt: str, max_tokens: int) -> Any:
        for piece in ["İyi ", "günler ", "efendim."]:
            yield _StreamPiece(piece)

    monkeypatch.setattr(mlx_lm, "load", fake_load)
    monkeypatch.setattr(mlx_lm, "generate", fake_generate)
    monkeypatch.setattr(mlx_lm, "stream_generate", fake_stream_generate)


async def test_lazy_loading() -> None:
    client = MLXClient()
    assert client.is_loaded is False
    await client.chat([ChatMessage(role="user", content="Merhaba")])
    assert client.is_loaded is True


async def test_chat_returns_response() -> None:
    client = MLXClient()
    resp = await client.chat([ChatMessage(role="user", content="Merhaba")])
    assert isinstance(resp, ChatResponse)
    assert resp.content == "İyi günler efendim."  # baştaki/sondaki boşluk kırpılmış
    assert resp.model == client.model_name
    assert resp.tokens == 3
    assert resp.latency_ms >= 0


async def test_unload_resets_state() -> None:
    client = MLXClient()
    await client.chat([ChatMessage(role="user", content="Merhaba")])
    assert client.is_loaded is True
    client.unload()
    assert client.is_loaded is False


async def test_chat_stream_yields_pieces() -> None:
    client = MLXClient()
    pieces = [p async for p in client.chat_stream([ChatMessage(role="user", content="hi")])]
    assert pieces == ["İyi ", "günler ", "efendim."]


async def test_chat_with_stream_true_collects() -> None:
    client = MLXClient()
    resp = await client.chat([ChatMessage(role="user", content="hi")], stream=True)
    assert resp.content == "İyi günler efendim."


async def test_list_models() -> None:
    client = MLXClient(model_name="my-model")
    assert await client.list_models() == ["my-model"]


async def test_health_check_true_when_mlx_present() -> None:
    client = MLXClient()
    assert await client.health_check() is True
