"""Orchestrator testleri — sahte client'lar + fakeredis kısa süreli hafıza."""

from __future__ import annotations

from collections.abc import AsyncIterator

import fakeredis.aioredis
import pytest

from jarvis.core import Lane, Orchestrator, Router
from jarvis.memory.short_term import ShortTermMemory
from jarvis.models import ChatMessage, ChatResponse
from jarvis.models.base import LLMClient


class RecordingClient(LLMClient):
    """Aldığı mesajları kaydeden, sabit yanıt veren sahte client."""

    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.last_messages: list[ChatMessage] | None = None

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        self.last_messages = messages
        return ChatResponse(content=f"{self.tag}-yanıt", model=self.tag, latency_ms=1.0)

    def chat_stream(
        self, messages: list[ChatMessage], model: str | None = None
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    async def list_models(self) -> list[str]:
        return [self.tag]

    async def health_check(self) -> bool:
        return True


@pytest.fixture
async def short_term() -> ShortTermMemory:
    redis = fakeredis.aioredis.FakeRedis()
    await redis.flushall()
    return ShortTermMemory(redis)


@pytest.fixture
def clients() -> tuple[RecordingClient, RecordingClient]:
    return RecordingClient("fast"), RecordingClient("deep")


async def test_fast_message_uses_fast_client(
    short_term: ShortTermMemory, clients: tuple[RecordingClient, RecordingClient]
) -> None:
    fast, deep = clients
    orch = Orchestrator(Router(), fast, deep, short_term=short_term)
    result = await orch.handle("Merhaba")
    assert result.lane == Lane.FAST
    assert result.model == "fast"
    assert fast.last_messages is not None
    assert deep.last_messages is None


async def test_deep_message_uses_deep_client(
    short_term: ShortTermMemory, clients: tuple[RecordingClient, RecordingClient]
) -> None:
    fast, deep = clients
    orch = Orchestrator(Router(), fast, deep, short_term=short_term)
    result = await orch.handle("Bu konuyu araştır lütfen")
    assert result.lane == Lane.DEEP
    assert result.model == "deep"
    assert deep.last_messages is not None


async def test_system_prompt_is_prepended(
    short_term: ShortTermMemory, clients: tuple[RecordingClient, RecordingClient]
) -> None:
    fast, deep = clients
    orch = Orchestrator(Router(), fast, deep, short_term=short_term)
    await orch.handle("Merhaba")
    assert fast.last_messages is not None
    assert fast.last_messages[0].role == "system"
    assert "Jarvis" in fast.last_messages[0].content
    assert fast.last_messages[-1].content == "Merhaba"


async def test_turn_is_stored_and_reused_as_history(
    short_term: ShortTermMemory, clients: tuple[RecordingClient, RecordingClient]
) -> None:
    fast, deep = clients
    orch = Orchestrator(Router(), fast, deep, short_term=short_term)

    await orch.handle("Merhaba", session_id="s1")
    # İkinci istekte geçmiş (user+assistant) bağlama girmeli.
    await orch.handle("Nasılsın", session_id="s1")

    assert fast.last_messages is not None
    contents = [m.content for m in fast.last_messages]
    assert "Merhaba" in contents  # önceki kullanıcı mesajı
    assert "fast-yanıt" in contents  # önceki asistan yanıtı
    assert contents[-1] == "Nasılsın"  # güncel mesaj sonda


async def test_sessions_are_isolated(
    short_term: ShortTermMemory, clients: tuple[RecordingClient, RecordingClient]
) -> None:
    fast, deep = clients
    orch = Orchestrator(Router(), fast, deep, short_term=short_term)
    await orch.handle("Merhaba", session_id="s1")
    await orch.handle("Selam", session_id="s2")
    history_s2 = await short_term.get_history("s2")
    assert all("Merhaba" not in m.content for m in history_s2)


async def test_stateless_without_short_term(
    clients: tuple[RecordingClient, RecordingClient],
) -> None:
    fast, deep = clients
    orch = Orchestrator(Router(), fast, deep, short_term=None)
    result = await orch.handle("Merhaba")
    assert result.content == "fast-yanıt"
    # Durumsuz: yalnızca system + user.
    assert fast.last_messages is not None
    assert len(fast.last_messages) == 2
