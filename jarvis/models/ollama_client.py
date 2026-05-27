"""Ollama HTTP API'si üzerinden async LLM client'ı."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator

import httpx

from jarvis.models.base import ChatMessage, ChatResponse, LLMClient
from jarvis.util import retry_async

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:14b"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_TIMEOUT = 120.0
DEFAULT_MAX_RETRIES = 2  # toplam 3 deneme


class OllamaClient(LLMClient):
    """Yerel Ollama sunucusuyla konuşan async client.

    Ollama'nın REST API'sini (`/api/chat`, `/api/embed`, `/api/tags`) httpx
    üzerinden kullanır.

    Attributes:
        base_url: Ollama sunucu adresi.
        default_model: Sohbet için model belirtilmediğinde kullanılacak model.
        embed_model: Embedding için kullanılacak model.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        default_model: str = DEFAULT_MODEL,
        embed_model: str = DEFAULT_EMBED_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """OllamaClient'ı başlatır.

        Args:
            base_url: Ollama sunucu adresi.
            default_model: Varsayılan sohbet modeli adı.
            embed_model: Varsayılan embedding modeli adı.
            timeout: HTTP istek zaman aşımı (saniye).
            max_retries: Geçici ağ hatalarında ek deneme sayısı.
        """
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.embed_model = embed_model
        self._timeout = timeout
        self._max_retries = max_retries

    async def _post_json(self, path: str, payload: dict) -> dict:
        """POST yapar, geçici ağ hatalarında yeniden dener, JSON döndürür."""

        async def _do() -> dict:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(f"{self.base_url}{path}", json=payload)
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]

        return await retry_async(
            _do, attempts=self._max_retries + 1, retry_on=(httpx.TransportError,)
        )

    async def _get_json(self, path: str) -> dict:
        """GET yapar, geçici ağ hatalarında yeniden dener, JSON döndürür."""

        async def _do() -> dict:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self.base_url}{path}")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]

        return await retry_async(
            _do, attempts=self._max_retries + 1, retry_on=(httpx.TransportError,)
        )

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        """Mesajları Ollama'ya gönderir ve tam yanıtı döndürür.

        Args:
            messages: Sıralı sohbet mesajları.
            model: Kullanılacak model; ``None`` ise :attr:`default_model`.
            stream: ``True`` ise yanıt akışla toplanır, yine tam metin döner.

        Returns:
            Modelin yanıtını içeren :class:`ChatResponse`.

        Raises:
            httpx.HTTPError: Sunucuya ulaşılamaz veya hata dönerse.
        """
        target_model = model or self.default_model

        if stream:
            return await self._chat_collected(messages, target_model)

        payload = {
            "model": target_model,
            "messages": [m.model_dump() for m in messages],
            "stream": False,
        }
        logger.debug("Ollama chat isteği: model=%s, mesaj=%d", target_model, len(messages))

        start = time.perf_counter()
        data = await self._post_json("/api/chat", payload)
        latency_ms = (time.perf_counter() - start) * 1000

        content = data.get("message", {}).get("content", "")
        tokens = data.get("eval_count")
        logger.info(
            "Ollama yanıt: model=%s, latency=%.0fms, tokens=%s",
            target_model,
            latency_ms,
            tokens,
        )
        return ChatResponse(
            content=content,
            model=target_model,
            latency_ms=latency_ms,
            tokens=tokens,
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """Ollama yanıtını parça parça akış olarak verir.

        Args:
            messages: Sıralı sohbet mesajları.
            model: Kullanılacak model; ``None`` ise :attr:`default_model`.

        Yields:
            Yanıtın art arda gelen metin parçaları.

        Raises:
            httpx.HTTPError: Sunucuya ulaşılamaz veya hata dönerse.
        """
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "messages": [m.model_dump() for m in messages],
            "stream": True,
        }
        logger.debug("Ollama stream isteği: model=%s", target_model)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    piece = chunk.get("message", {}).get("content", "")
                    if piece:
                        yield piece
                    if chunk.get("done"):
                        break

    async def _chat_collected(self, messages: list[ChatMessage], model: str) -> ChatResponse:
        """Akışı toplayıp tek :class:`ChatResponse` olarak döndürür."""
        start = time.perf_counter()
        parts: list[str] = []
        async for piece in self.chat_stream(messages, model):
            parts.append(piece)
        latency_ms = (time.perf_counter() - start) * 1000
        return ChatResponse(
            content="".join(parts),
            model=model,
            latency_ms=latency_ms,
            tokens=None,
        )

    async def embed(
        self,
        texts: str | list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """Verilen metin(ler) için embedding vektörleri üretir.

        Args:
            texts: Tek bir metin veya metin listesi.
            model: Kullanılacak embedding modeli; ``None`` ise :attr:`embed_model`.

        Returns:
            Her girdi için bir vektör içeren liste. Tek metin verilse bile
            tek elemanlı liste döner.

        Raises:
            httpx.HTTPError: Sunucuya ulaşılamaz veya hata dönerse.
        """
        target_model = model or self.embed_model
        inputs = [texts] if isinstance(texts, str) else texts
        payload = {"model": target_model, "input": inputs}
        logger.debug("Ollama embed isteği: model=%s, girdi=%d", target_model, len(inputs))

        data = await self._post_json("/api/embed", payload)
        embeddings: list[list[float]] = data.get("embeddings", [])
        return embeddings

    async def list_models(self) -> list[str]:
        """Ollama'da yüklü modellerin adlarını döndürür.

        Returns:
            Model adlarından oluşan liste; hata olursa boş liste.
        """
        data = await self._get_json("/api/tags")
        return [m["name"] for m in data.get("models", [])]

    async def health_check(self) -> bool:
        """Ollama sunucusuna ulaşılabilirliği kontrol eder.

        Returns:
            Sunucu yanıt veriyorsa ``True``, aksi halde ``False``.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
            return True
        except (httpx.HTTPError, OSError) as exc:
            logger.warning("Ollama health check başarısız: %s", exc)
            return False
