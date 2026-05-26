"""Router (kural tabanlı niyet yönlendirici) testleri."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from jarvis.core import Lane, Router, RouterDecision
from jarvis.models import ChatMessage, ChatResponse
from jarvis.models.base import LLMClient


@pytest.fixture
def router() -> Router:
    return Router()


# ── Fast Lane ──


@pytest.mark.parametrize(
    "message",
    ["Merhaba", "Saat kaç?", "Işıkları aç", "Teşekkürler efendim", "Evet"],
)
def test_short_simple_goes_fast(router: Router, message: str) -> None:
    assert router.route(message).lane == Lane.FAST


# ── Deep Think ──


@pytest.mark.parametrize(
    "message",
    [
        "Bu konuyu araştır",
        "Bana bir Python fonksiyon yaz",
        "Şu iki yaklaşımı karşılaştır",
        "Bunu neden böyle yaptığını açıkla",
        "Bu metni özetle lütfen",
        "Research the latest AI news",
    ],
)
def test_deep_keywords_go_deep(router: Router, message: str) -> None:
    decision = router.route(message)
    assert decision.lane == Lane.DEEP
    assert "anahtar kelime" in decision.reason


def test_long_message_goes_deep(router: Router) -> None:
    msg = "kelime " * 40  # > 200 karakter, anahtar kelime yok
    decision = router.route(msg)
    assert decision.lane == Lane.DEEP
    assert "uzun mesaj" in decision.reason


def test_multiple_questions_go_deep(router: Router) -> None:
    decision = router.route("Bugün hava nasıl olur sence? Sonra ne yapsak peki?")
    assert decision.lane == Lane.DEEP


def test_many_sentences_go_deep(router: Router) -> None:
    decision = router.route("Bir. İki. Üç. Dört.")
    assert decision.lane == Lane.DEEP
    assert "cümleli" in decision.reason


def test_decision_is_model(router: Router) -> None:
    assert isinstance(router.route("Merhaba"), RouterDecision)


def test_custom_thresholds() -> None:
    router = Router(max_fast_chars=10)
    assert router.route("kısa").lane == Lane.FAST
    assert router.route("bu mesaj on karakterden uzun").lane == Lane.DEEP


# ── pick_client ──


class _FakeClient(LLMClient):
    def __init__(self, tag: str) -> None:
        self.tag = tag

    async def chat(
        self, messages: list[ChatMessage], model: str | None = None, stream: bool = False
    ) -> ChatResponse:
        return ChatResponse(content=self.tag, model=self.tag, latency_ms=0.0)

    def chat_stream(
        self, messages: list[ChatMessage], model: str | None = None
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    async def list_models(self) -> list[str]:
        return [self.tag]

    async def health_check(self) -> bool:
        return True


def test_pick_client_fast(router: Router) -> None:
    fast, deep = _FakeClient("fast"), _FakeClient("deep")
    client, decision = router.pick_client("Merhaba", fast, deep)
    assert client is fast
    assert decision.lane == Lane.FAST


def test_pick_client_deep(router: Router) -> None:
    fast, deep = _FakeClient("fast"), _FakeClient("deep")
    client, decision = router.pick_client("Bunu araştır lütfen", fast, deep)
    assert client is deep
    assert decision.lane == Lane.DEEP
