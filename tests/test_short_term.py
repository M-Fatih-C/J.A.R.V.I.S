"""ShortTermMemory için fakeredis tabanlı birim testler (gerçek Redis gerekmez)."""

from __future__ import annotations

import fakeredis.aioredis
import pytest

from jarvis.memory.short_term import ShortTermMemory
from jarvis.models import ChatMessage


@pytest.fixture
async def memory() -> ShortTermMemory:
    """Her test için temiz bir fakeredis destekli hafıza."""
    redis = fakeredis.aioredis.FakeRedis()
    await redis.flushall()
    return ShortTermMemory(redis, max_messages=5, ttl_seconds=3600)


async def test_add_and_get_history(memory: ShortTermMemory) -> None:
    await memory.add_message("s1", ChatMessage(role="user", content="Merhaba"))
    await memory.add_message("s1", ChatMessage(role="assistant", content="Efendim?"))

    history = await memory.get_history("s1")
    assert [m.content for m in history] == ["Merhaba", "Efendim?"]
    assert [m.role for m in history] == ["user", "assistant"]


async def test_history_is_ordered_oldest_first(memory: ShortTermMemory) -> None:
    for i in range(3):
        await memory.add_message("s1", ChatMessage(role="user", content=f"m{i}"))
    history = await memory.get_history("s1")
    assert [m.content for m in history] == ["m0", "m1", "m2"]


async def test_max_messages_trim(memory: ShortTermMemory) -> None:
    for i in range(8):  # max_messages=5
        await memory.add_message("s1", ChatMessage(role="user", content=f"m{i}"))
    history = await memory.get_history("s1")
    assert len(history) == 5
    assert [m.content for m in history] == ["m3", "m4", "m5", "m6", "m7"]


async def test_get_history_limit(memory: ShortTermMemory) -> None:
    for i in range(5):
        await memory.add_message("s1", ChatMessage(role="user", content=f"m{i}"))
    history = await memory.get_history("s1", limit=2)
    assert [m.content for m in history] == ["m3", "m4"]


async def test_sessions_are_isolated(memory: ShortTermMemory) -> None:
    await memory.add_message("s1", ChatMessage(role="user", content="a"))
    await memory.add_message("s2", ChatMessage(role="user", content="b"))
    assert (await memory.get_history("s1"))[0].content == "a"
    assert (await memory.get_history("s2"))[0].content == "b"


async def test_clear(memory: ShortTermMemory) -> None:
    await memory.add_message("s1", ChatMessage(role="user", content="a"))
    await memory.clear("s1")
    assert await memory.get_history("s1") == []
    assert await memory.count("s1") == 0


async def test_count(memory: ShortTermMemory) -> None:
    assert await memory.count("s1") == 0
    await memory.add_message("s1", ChatMessage(role="user", content="a"))
    await memory.add_message("s1", ChatMessage(role="user", content="b"))
    assert await memory.count("s1") == 2


async def test_ttl_is_set(memory: ShortTermMemory) -> None:
    await memory.add_message("s1", ChatMessage(role="user", content="a"))
    redis = memory._redis
    ttl = await redis.ttl("jarvis:chat:s1")
    assert 0 < ttl <= 3600
