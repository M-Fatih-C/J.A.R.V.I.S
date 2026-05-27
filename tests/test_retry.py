"""retry_async yardımcısı testleri."""

from __future__ import annotations

import pytest

import jarvis.util.retry as retry_mod
from jarvis.util import retry_async


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Testlerde gerçek beklemeyi kaldır."""

    async def _instant(_seconds: float) -> None:
        return None

    monkeypatch.setattr(retry_mod.asyncio, "sleep", _instant)


async def test_succeeds_first_try() -> None:
    calls = {"n": 0}

    async def func() -> str:
        calls["n"] += 1
        return "ok"

    assert await retry_async(func, attempts=3) == "ok"
    assert calls["n"] == 1


async def test_retries_then_succeeds() -> None:
    calls = {"n": 0}

    async def func() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("geçici")
        return "ok"

    assert await retry_async(func, attempts=3, retry_on=(ValueError,)) == "ok"
    assert calls["n"] == 3


async def test_raises_after_exhausting() -> None:
    async def func() -> str:
        raise ValueError("hep başarısız")

    with pytest.raises(ValueError, match="hep başarısız"):
        await retry_async(func, attempts=3, retry_on=(ValueError,))


async def test_does_not_retry_unlisted_exception() -> None:
    calls = {"n": 0}

    async def func() -> str:
        calls["n"] += 1
        raise KeyError("retry edilmez")

    with pytest.raises(KeyError):
        await retry_async(func, attempts=3, retry_on=(ValueError,))
    assert calls["n"] == 1
