"""Async yeniden deneme (retry) yardımcısı — üstel backoff ile."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_async(
    func: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    """Bir async çağrıyı geçici hatalarda üstel backoff ile yeniden dener.

    Args:
        func: Argümansız, awaitable döndüren çağrı (her denemede yeniden çağrılır).
        attempts: Toplam deneme sayısı (>=1).
        base_delay: İlk bekleme süresi; her denemede 2 katına çıkar.
        retry_on: Yeniden denemeyi tetikleyen istisna türleri.

    Returns:
        ``func`` başarılı olursa sonucu.

    Raises:
        BaseException: Son deneme de başarısız olursa son istisna yeniden fırlatılır.
    """
    last_exc: BaseException | None = None
    for attempt in range(attempts):
        try:
            return await func()
        except retry_on as exc:
            last_exc = exc
            if attempt < attempts - 1:
                delay = base_delay * (2**attempt)
                logger.warning(
                    "Deneme %d/%d başarısız (%s); %.2fs sonra yeniden denenecek.",
                    attempt + 1,
                    attempts,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc
