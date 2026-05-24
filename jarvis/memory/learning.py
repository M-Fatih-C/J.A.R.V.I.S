"""Öğrenme motoru — oturum geçmişini özetleyip vektör hafızaya pekiştirir."""

from __future__ import annotations

import asyncio
import logging

from jarvis.memory.short_term import ShortTermMemory
from jarvis.memory.vector_store import VectorMemory
from jarvis.models import ChatMessage
from jarvis.models.base import LLMClient

logger = logging.getLogger(__name__)

DEFAULT_MIN_MESSAGES = 4

SUMMARY_SYSTEM_PROMPT = (
    "Sen bir kişisel asistanın hafıza özetleyicisisin. Aşağıdaki konuşmayı, "
    "kullanıcı hakkında öğrenilen kalıcı bilgileri ve önemli noktaları "
    "koruyarak kısa ve öz biçimde özetle. Yalnızca özet metnini döndür."
)


class LearningEngine:
    """Konuşmaları özetleyerek uzun vadeli (vektör) hafızaya aktarır.

    Attributes:
        min_messages: Özet üretmek için gereken asgari mesaj sayısı.
    """

    def __init__(
        self,
        short_term: ShortTermMemory,
        vector: VectorMemory,
        llm: LLMClient,
        min_messages: int = DEFAULT_MIN_MESSAGES,
    ) -> None:
        """LearningEngine'i başlatır.

        Args:
            short_term: Kısa süreli hafıza (kaynak).
            vector: Vektör hafıza (özetlerin hedefi).
            llm: Özetleme için kullanılacak LLM client'ı.
            min_messages: Özet için gereken asgari mesaj sayısı.
        """
        self._short_term = short_term
        self._vector = vector
        self._llm = llm
        self.min_messages = min_messages

    async def summarize_session(self, session_id: str) -> str | None:
        """Oturum geçmişini LLM ile özetler.

        Args:
            session_id: Özetlenecek oturum.

        Returns:
            Özet metni; geçmiş ``min_messages``'tan azsa ``None``.
        """
        history = await self._short_term.get_history(session_id)
        if len(history) < self.min_messages:
            logger.debug(
                "Özet atlandı: session=%s, mesaj=%d < %d",
                session_id,
                len(history),
                self.min_messages,
            )
            return None

        transcript = "\n".join(f"{m.role}: {m.content}" for m in history)
        messages = [
            ChatMessage(role="system", content=SUMMARY_SYSTEM_PROMPT),
            ChatMessage(role="user", content=transcript),
        ]
        resp = await self._llm.chat(messages)
        return resp.content.strip()

    async def consolidate_session(self, session_id: str, clear_after: bool = False) -> str | None:
        """Oturumu özetler ve özeti vektör hafızaya kaydeder.

        Args:
            session_id: Pekiştirilecek oturum.
            clear_after: ``True`` ise pekiştirme sonrası kısa süreli geçmiş silinir.

        Returns:
            Kaydedilen özet kaydının kimliği; özet üretilemezse ``None``.
        """
        summary = await self.summarize_session(session_id)
        if not summary:
            return None

        doc_id = await self._vector.add(
            summary,
            metadata={"type": "summary", "session_id": session_id},
        )
        if clear_after:
            await self._short_term.clear(session_id)
        logger.info("Oturum pekiştirildi: session=%s, doc=%s", session_id, doc_id)
        return doc_id

    async def run_periodic(
        self, session_id: str, interval_seconds: float, clear_after: bool = False
    ) -> None:
        """Bir oturumu belirli aralıklarla pekiştiren arka plan döngüsü.

        İptal edilene (``asyncio.CancelledError``) kadar çalışır. Tekil
        pekiştirme hataları loglanır ve döngü sürer.

        Args:
            session_id: Periyodik olarak pekiştirilecek oturum.
            interval_seconds: Pekiştirmeler arası süre (saniye).
            clear_after: Her pekiştirmeden sonra geçmişi temizle.
        """
        logger.info(
            "Öğrenme döngüsü başladı: session=%s, aralık=%.0fs",
            session_id,
            interval_seconds,
        )
        while True:
            await asyncio.sleep(interval_seconds)
            try:
                await self.consolidate_session(session_id, clear_after=clear_after)
            except Exception:  # noqa: BLE001 — döngü hatadan etkilenmemeli
                logger.exception("Pekiştirme başarısız: session=%s", session_id)
