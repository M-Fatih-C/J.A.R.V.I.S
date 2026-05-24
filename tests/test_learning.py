"""LearningEngine testleri — sahte LLM + fakeredis + gömülü vektör hafıza."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import fakeredis.aioredis
import pytest

from jarvis.memory.learning import LearningEngine
from jarvis.memory.short_term import ShortTermMemory
from jarvis.memory.vector_store import VectorMemory
from jarvis.models import ChatMessage, ChatResponse
from jarvis.models.base import LLMClient


class FakeLLM(LLMClient):
    """Sabit özet döndüren, gönderilen mesajları kaydeden sahte LLM."""

    def __init__(self, reply: str = "Özet: kullanıcı kedileri sever.") -> None:
        self.reply = reply
        self.received: list[ChatMessage] | None = None

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        self.received = messages
        return ChatResponse(content=self.reply, model="fake", latency_ms=1.0)

    def chat_stream(
        self, messages: list[ChatMessage], model: str | None = None
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    async def list_models(self) -> list[str]:
        return ["fake"]

    async def health_check(self) -> bool:
        return True


async def _const_embedder(texts: list[str]) -> list[list[float]]:
    return [[1.0, 0.0, 0.0] for _ in texts]


@pytest.fixture
async def engine(tmp_path: Path) -> tuple[LearningEngine, ShortTermMemory, FakeLLM]:
    redis = fakeredis.aioredis.FakeRedis()
    await redis.flushall()
    short_term = ShortTermMemory(redis)
    vector = VectorMemory(
        embedder=_const_embedder,
        path=str(tmp_path / "chroma"),
        collection_name="test_learn",
    )
    llm = FakeLLM()
    return LearningEngine(short_term, vector, llm, min_messages=2), short_term, llm


async def _seed(short_term: ShortTermMemory, session: str, n: int) -> None:
    for i in range(n):
        role = "user" if i % 2 == 0 else "assistant"
        await short_term.add_message(session, ChatMessage(role=role, content=f"m{i}"))


async def test_summarize_too_few_returns_none(
    engine: tuple[LearningEngine, ShortTermMemory, FakeLLM],
) -> None:
    eng, short_term, _ = engine
    await _seed(short_term, "s1", 1)  # min_messages=2
    assert await eng.summarize_session("s1") is None


async def test_summarize_returns_text(
    engine: tuple[LearningEngine, ShortTermMemory, FakeLLM],
) -> None:
    eng, short_term, llm = engine
    await _seed(short_term, "s1", 4)
    summary = await eng.summarize_session("s1")
    assert summary == "Özet: kullanıcı kedileri sever."
    # LLM'e sistem prompt + transcript gitti mi?
    assert llm.received is not None
    assert llm.received[0].role == "system"
    assert "m0" in llm.received[1].content


async def test_consolidate_stores_in_vector(
    engine: tuple[LearningEngine, ShortTermMemory, FakeLLM],
) -> None:
    eng, short_term, _ = engine
    await _seed(short_term, "s1", 4)
    doc_id = await eng.consolidate_session("s1")
    assert doc_id is not None
    assert await eng._vector.count() == 1


async def test_consolidate_too_few_returns_none(
    engine: tuple[LearningEngine, ShortTermMemory, FakeLLM],
) -> None:
    eng, short_term, _ = engine
    await _seed(short_term, "s1", 1)
    assert await eng.consolidate_session("s1") is None
    assert await eng._vector.count() == 0


async def test_consolidate_clear_after(
    engine: tuple[LearningEngine, ShortTermMemory, FakeLLM],
) -> None:
    eng, short_term, _ = engine
    await _seed(short_term, "s1", 4)
    await eng.consolidate_session("s1", clear_after=True)
    assert await short_term.count("s1") == 0
