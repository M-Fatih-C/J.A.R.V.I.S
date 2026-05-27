"""Kısa süreli hafıza — Redis tabanlı, oturum bazlı konuşma penceresi."""

from __future__ import annotations

import logging
from collections.abc import Awaitable
from typing import cast

from redis.asyncio import Redis

from jarvis.models import ChatMessage

logger = logging.getLogger(__name__)

DEFAULT_MAX_MESSAGES = 50
DEFAULT_TTL_SECONDS = 60 * 60 * 24  # 24 saat
_KEY_PREFIX = "jarvis:chat:"


class ShortTermMemory:
    """Oturum başına son N mesajı Redis listesinde tutan kısa süreli hafıza.

    Her oturum bir Redis listesidir (`jarvis:chat:<session_id>`). Liste
    ``max_messages`` ile sınırlanır ve her yazımda TTL yenilenir.

    Attributes:
        max_messages: Oturum başına saklanacak azami mesaj sayısı.
        ttl_seconds: Oturum anahtarının yaşam süresi (saniye).
    """

    def __init__(
        self,
        redis: Redis,
        max_messages: int = DEFAULT_MAX_MESSAGES,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        """ShortTermMemory'yi başlatır.

        Args:
            redis: Async Redis istemcisi (DI; testlerde fakeredis kullanılır).
            max_messages: Oturum başına azami mesaj sayısı.
            ttl_seconds: Oturum TTL'i (saniye).
        """
        self._redis = redis
        self.max_messages = max_messages
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def _key(session_id: str) -> str:
        """Oturum için Redis anahtarını üretir."""
        return f"{_KEY_PREFIX}{session_id}"

    async def add_message(self, session_id: str, message: ChatMessage) -> None:
        """Oturuma bir mesaj ekler, listeyi kırpar ve TTL'i yeniler.

        Args:
            session_id: Oturum tanımlayıcısı.
            message: Eklenecek sohbet mesajı.
        """
        key = self._key(session_id)
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.rpush(key, message.model_dump_json())
            pipe.ltrim(key, -self.max_messages, -1)
            pipe.expire(key, self.ttl_seconds)
            await pipe.execute()
        logger.debug("Mesaj eklendi: session=%s, role=%s", session_id, message.role)

    async def get_history(self, session_id: str, limit: int | None = None) -> list[ChatMessage]:
        """Oturumun mesaj geçmişini (eskiden yeniye) döndürür.

        Args:
            session_id: Oturum tanımlayıcısı.
            limit: Yalnızca son ``limit`` mesajı döndür; ``None`` ise tümü.

        Returns:
            Sıralı :class:`ChatMessage` listesi.
        """
        key = self._key(session_id)
        start = -limit if limit else 0
        raw = await cast("Awaitable[list[bytes]]", self._redis.lrange(key, start, -1))
        return [ChatMessage.model_validate_json(item) for item in raw]

    async def clear(self, session_id: str) -> None:
        """Oturumun tüm geçmişini siler.

        Args:
            session_id: Oturum tanımlayıcısı.
        """
        await self._redis.delete(self._key(session_id))
        logger.debug("Oturum temizlendi: session=%s", session_id)

    async def ping(self) -> bool:
        """Redis'e erişilebilirliği kontrol eder.

        Returns:
            Redis yanıt veriyorsa ``True``, aksi halde ``False``.
        """
        try:
            await cast("Awaitable[bool]", self._redis.ping())
            return True
        except Exception:  # noqa: BLE001 — erişilemezlik False döndürür
            return False

    async def count(self, session_id: str) -> int:
        """Oturumdaki mesaj sayısını döndürür.

        Args:
            session_id: Oturum tanımlayıcısı.

        Returns:
            Saklanan mesaj sayısı.
        """
        return await cast("Awaitable[int]", self._redis.llen(self._key(session_id)))
