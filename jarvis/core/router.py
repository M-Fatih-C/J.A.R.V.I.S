"""Model router — niyet tespitiyle isteği Fast Lane ↔ Deep Think'e yönlendirir.

Faz 3'te kural tabanlı (heuristik) çalışır: mesaj uzunluğu, derin düşünme
gerektiren anahtar kelimeler ve cümle/soru karmaşıklığına bakar. Model
gerektirmez, deterministiktir; sonraki fazlarda MLX sınıflandırmasıyla
zenginleştirilebilir.
"""

from __future__ import annotations

import logging
import re
from enum import StrEnum

from pydantic import BaseModel

from jarvis.models.base import LLMClient

logger = logging.getLogger(__name__)


class Lane(StrEnum):
    """İşlem hattı.

    Attributes:
        FAST: Hızlı, hafif yanıtlar (MLX / Phi-3.5 Mini).
        DEEP: Derin düşünme, tool calling (Ollama / Qwen 2.5 14B).
    """

    FAST = "fast"
    DEEP = "deep"


class RouterDecision(BaseModel):
    """Yönlendirme kararı.

    Attributes:
        lane: Seçilen işlem hattı.
        reason: Kararın insan-okur gerekçesi (gözlemlenebilirlik için).
    """

    lane: Lane
    reason: str


# Derin düşünme/araç gerektiren anahtar kelimeler (TR + EN, küçük harf).
# Türkçe eklemeli yapı için alt-dize eşleşmesi kullanılır (ör. "araştır" →
# "araştırır", "araştırma" hepsini yakalar).
DEFAULT_DEEP_KEYWORDS: frozenset[str] = frozenset(
    {
        # araştırma / web
        "araştır",
        "research",
        "kaynak",
        "internette",
        # kod
        "kod yaz",
        "kodla",
        "fonksiyon yaz",
        "script",
        "code",
        "function",
        "debug",
        "hata ayıkla",
        # analiz / akıl yürütme
        "analiz",
        "analyze",
        "karşılaştır",
        "compare",
        "açıkla",
        "explain",
        "neden",
        "why",
        "adım adım",
        "step by step",
        # üretim / dönüştürme
        "özetle",
        "summarize",
        "rapor",
        "report",
        "planla",
        "plan yap",
        "çevir",
        "translate",
        "hesapla",
        "calculate",
    }
)

DEFAULT_MAX_FAST_CHARS = 200
DEFAULT_MAX_FAST_SENTENCES = 2


class Router:
    """Kural tabanlı niyet yönlendiricisi.

    Attributes:
        max_fast_chars: Bu uzunluğu aşan mesajlar Deep Think'e gider.
        max_fast_sentences: Bu sayıyı aşan cümleli mesajlar Deep Think'e gider.
    """

    def __init__(
        self,
        max_fast_chars: int = DEFAULT_MAX_FAST_CHARS,
        max_fast_sentences: int = DEFAULT_MAX_FAST_SENTENCES,
        deep_keywords: frozenset[str] = DEFAULT_DEEP_KEYWORDS,
    ) -> None:
        """Router'ı başlatır.

        Args:
            max_fast_chars: Fast Lane için azami karakter sayısı.
            max_fast_sentences: Fast Lane için azami cümle sayısı.
            deep_keywords: Deep Think'i tetikleyen anahtar kelimeler (küçük harf).
        """
        self.max_fast_chars = max_fast_chars
        self.max_fast_sentences = max_fast_sentences
        self._deep_keywords = deep_keywords

    def route(self, message: str) -> RouterDecision:
        """Bir mesajı uygun işlem hattına yönlendirir.

        Args:
            message: Kullanıcı mesajı.

        Returns:
            Seçilen hat ve gerekçeyi içeren :class:`RouterDecision`.
        """
        text = message.strip()
        lower = text.lower()

        for kw in self._deep_keywords:
            if kw in lower:
                return self._decide(Lane.DEEP, f"derin anahtar kelime: '{kw}'")

        if len(text) > self.max_fast_chars:
            return self._decide(
                Lane.DEEP, f"uzun mesaj ({len(text)} > {self.max_fast_chars} karakter)"
            )

        if text.count("?") >= 2:
            return self._decide(Lane.DEEP, "birden çok soru")

        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        if len(sentences) > self.max_fast_sentences:
            return self._decide(Lane.DEEP, f"çok cümleli istek ({len(sentences)})")

        return self._decide(Lane.FAST, "kısa/basit istek")

    @staticmethod
    def _decide(lane: Lane, reason: str) -> RouterDecision:
        logger.debug("Router kararı: %s — %s", lane.value, reason)
        return RouterDecision(lane=lane, reason=reason)

    def pick_client(
        self,
        message: str,
        fast_client: LLMClient,
        deep_client: LLMClient,
    ) -> tuple[LLMClient, RouterDecision]:
        """Mesajı yönlendirir ve uygun client'ı seçer.

        Args:
            message: Kullanıcı mesajı.
            fast_client: Fast Lane client'ı (örn. MLXClient).
            deep_client: Deep Think client'ı (örn. OllamaClient).

        Returns:
            Seçilen client ve karar.
        """
        decision = self.route(message)
        client = fast_client if decision.lane == Lane.FAST else deep_client
        return client, decision
