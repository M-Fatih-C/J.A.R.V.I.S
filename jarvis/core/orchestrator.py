"""Orchestrator — Router, model client'ları ve hafızayı tek akışta birleştirir.

Bir kullanıcı mesajını alır, niyete göre Fast Lane (MLX) veya Deep Think
(Ollama) hattını seçer, kısa süreli hafızadan bağlamı ekler, yanıtı üretir ve
konuşmayı hafızaya geri yazar. Kısa süreli hafıza (Redis) erişilemezse akış
durumsuz (stateless) olarak sürer.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel

from jarvis.core.router import Lane, Router
from jarvis.memory.short_term import ShortTermMemory
from jarvis.models import ChatMessage
from jarvis.models.base import LLMClient

logger = logging.getLogger(__name__)

DEFAULT_HISTORY_LIMIT = 20

JARVIS_SYSTEM_PROMPT = (
    "Sen Jarvis'sin: sakin, kendinden emin, hafif İngiliz uşağı havasında bir "
    "kişisel asistan. Kullanıcıya 'efendim' diye hitap edersin. Kısa ve öz "
    "yanıt verirsin, gereksiz açıklama yapmazsın."
)


class ChatResult(BaseModel):
    """Orchestrator yanıtı.

    Attributes:
        content: Üretilen yanıt metni.
        model: Yanıtı üreten model adı.
        lane: Seçilen işlem hattı (fast/deep).
        reason: Yönlendirme gerekçesi.
        latency_ms: LLM çağrısının süresi (ms).
        tokens: Üretilen token sayısı (biliniyorsa).
    """

    content: str
    model: str
    lane: Lane
    reason: str
    latency_ms: float
    tokens: int | None = None


class Orchestrator:
    """İstekleri uçtan uca yöneten ana koordinatör."""

    def __init__(
        self,
        router: Router,
        fast_client: LLMClient,
        deep_client: LLMClient,
        short_term: ShortTermMemory | None = None,
        system_prompt: str = JARVIS_SYSTEM_PROMPT,
        history_limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> None:
        """Orchestrator'ı başlatır.

        Args:
            router: Niyet yönlendiricisi.
            fast_client: Fast Lane client'ı (örn. MLXClient).
            deep_client: Deep Think client'ı (örn. OllamaClient).
            short_term: Kısa süreli hafıza; ``None`` ise durumsuz çalışır.
            system_prompt: Her konuşmaya eklenen sistem prompt'u.
            history_limit: Bağlama dahil edilecek azami geçmiş mesaj sayısı.
        """
        self._router = router
        self._fast = fast_client
        self._deep = deep_client
        self._short_term = short_term
        self._system_prompt = system_prompt
        self._history_limit = history_limit

    async def handle(self, message: str, session_id: str = "default") -> ChatResult:
        """Bir kullanıcı mesajını işler ve yanıtı döndürür.

        Args:
            message: Kullanıcı mesajı.
            session_id: Konuşma oturumu tanımlayıcısı.

        Returns:
            Yanıt ve yönlendirme bilgisini içeren :class:`ChatResult`.
        """
        decision = self._router.route(message)
        client = self._fast if decision.lane == Lane.FAST else self._deep

        history = await self._load_history(session_id)
        messages = [
            ChatMessage(role="system", content=self._system_prompt),
            *history,
            ChatMessage(role="user", content=message),
        ]

        logger.info(
            "İstek yönlendirildi: lane=%s, session=%s (%s)",
            decision.lane.value,
            session_id,
            decision.reason,
        )
        response = await client.chat(messages)

        await self._store_turn(session_id, message, response.content)

        return ChatResult(
            content=response.content,
            model=response.model,
            lane=decision.lane,
            reason=decision.reason,
            latency_ms=response.latency_ms,
            tokens=response.tokens,
        )

    async def _load_history(self, session_id: str) -> list[ChatMessage]:
        """Kısa süreli hafızadan geçmişi yükler; hata olursa boş liste döner."""
        if self._short_term is None:
            return []
        try:
            return await self._short_term.get_history(session_id, limit=self._history_limit)
        except Exception:  # noqa: BLE001 — hafıza yoksa durumsuz devam
            logger.warning("Kısa süreli hafıza okunamadı; durumsuz devam.")
            return []

    async def _store_turn(self, session_id: str, user_message: str, assistant_message: str) -> None:
        """Kullanıcı ve asistan mesajlarını hafızaya yazar; hatayı yutmaz, loglar."""
        if self._short_term is None:
            return
        try:
            await self._short_term.add_message(
                session_id, ChatMessage(role="user", content=user_message)
            )
            await self._short_term.add_message(
                session_id, ChatMessage(role="assistant", content=assistant_message)
            )
        except Exception:  # noqa: BLE001 — yazım hatası yanıtı engellememeli
            logger.warning("Kısa süreli hafızaya yazılamadı.")
