"""LLM client'ları için ortak soyutlamalar ve veri modelleri."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    """Tek bir sohbet mesajı.

    Attributes:
        role: Mesajın sahibi (``system``, ``user`` veya ``assistant``).
        content: Mesaj metni.
    """

    role: Role
    content: str


class ChatResponse(BaseModel):
    """Bir LLM sohbet çağrısının sonucu.

    Attributes:
        content: Modelin ürettiği metin.
        model: Yanıtı üreten model adı.
        latency_ms: Çağrının toplam süresi (milisaniye).
        tokens: Üretilen token sayısı (biliniyorsa).
    """

    content: str
    model: str
    latency_ms: float
    tokens: int | None = Field(default=None)


class LLMClient(ABC):
    """Tüm LLM client'larının uygulaması gereken soyut arayüz."""

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        """Mesaj listesini modele gönderir ve tam yanıtı döndürür.

        Args:
            messages: Sıralı sohbet mesajları.
            model: Kullanılacak model; ``None`` ise varsayılan model.
            stream: İçeride akış kullanılıp kullanılmayacağı.

        Returns:
            Modelin tam yanıtını içeren :class:`ChatResponse`.
        """
        raise NotImplementedError

    @abstractmethod
    def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """Modelin yanıtını token/parça akışı olarak verir.

        Async generator döndürür; ``async for`` ile tüketilir.

        Args:
            messages: Sıralı sohbet mesajları.
            model: Kullanılacak model; ``None`` ise varsayılan model.

        Yields:
            Yanıtın art arda gelen metin parçaları.
        """
        raise NotImplementedError

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Sunucuda mevcut modellerin adlarını döndürür."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Sunucuya ulaşılabilirliği kontrol eder.

        Returns:
            Sunucu erişilebilirse ``True``, aksi halde ``False``.
        """
        raise NotImplementedError
