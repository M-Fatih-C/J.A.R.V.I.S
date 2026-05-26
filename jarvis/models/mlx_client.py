"""Apple MLX tabanlı hızlı yerel çıkarım client'ı (Fast Lane).

Phi-3.5 Mini gibi küçük bir modeli MLX ile çalıştırır. Model **lazy** yüklenir
(ilk istekte) ve RAM'i boşaltmak için :meth:`MLXClient.unload` ile bırakılabilir.
``mlx_lm`` yalnızca model yüklenirken import edilir; böylece modül MLX kurulu
olmasa da import edilebilir (ör. testlerde mock'lanabilir).
"""

from __future__ import annotations

import asyncio
import importlib.util
import logging
import threading
import time
from collections.abc import AsyncIterator
from typing import Any

from jarvis.models.base import ChatMessage, ChatResponse, LLMClient

logger = logging.getLogger(__name__)

DEFAULT_MLX_MODEL = "mlx-community/Phi-3.5-mini-instruct-4bit"
DEFAULT_MAX_TOKENS = 512


class MLXClient(LLMClient):
    """MLX üzerinde küçük bir dil modeli çalıştıran async client.

    Attributes:
        model_name: Yüklenecek MLX model kimliği (HuggingFace deposu).
        max_tokens: Üretilecek azami token sayısı.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MLX_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        """MLXClient'ı başlatır (model henüz yüklenmez).

        Args:
            model_name: MLX model kimliği.
            max_tokens: Yanıt başına azami token.
        """
        self.model_name = model_name
        self.max_tokens = max_tokens
        self._model: Any = None
        self._tokenizer: Any = None
        self._lock = threading.Lock()

    # ── Model yaşam döngüsü ──

    def _ensure_loaded(self) -> None:
        """Model yüklü değilse yükler (thread-safe, senkron)."""
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            from mlx_lm import load

            logger.info("MLX model yükleniyor: %s", self.model_name)
            loaded: Any = load(self.model_name)
            self._model, self._tokenizer = loaded[0], loaded[1]
            self._register_eos()
            logger.info("MLX model hazır: %s", self.model_name)

    def _register_eos(self) -> None:
        """Sohbet turu sonu token'ını (ör. Phi-3.5 '<|end|>') durdurma kümesine ekler.

        Bazı modellerde tokenizer'ın varsayılan ``eos_token_ids`` kümesi sohbet
        şablonunun tur-bitiş token'ını içermez; bu durumda model durmaz. Modelin
        kendi ``eos_token_id``'sini durdurma kümesine ekleyerek bunu garanti ederiz.
        """
        eos_id = getattr(self._tokenizer, "eos_token_id", None)
        eos_set = getattr(self._tokenizer, "eos_token_ids", None)
        if eos_id is not None and eos_set is not None:
            try:
                eos_set.add(eos_id)
            except Exception:  # noqa: BLE001 — durdurma token'ı eklenemezse kritik değil
                pass

    def unload(self) -> None:
        """Modeli bellekten bırakır ve MLX önbelleğini temizler."""
        with self._lock:
            self._model = None
            self._tokenizer = None
        try:
            import mlx.core as mx

            mx.clear_cache()
        except Exception:  # noqa: BLE001 — önbellek temizliği kritik değil
            pass
        logger.info("MLX model bellekten bırakıldı.")

    @property
    def is_loaded(self) -> bool:
        """Modelin yüklü olup olmadığını döndürür."""
        return self._model is not None

    def _build_prompt(self, messages: list[ChatMessage]) -> str:
        """Mesajları modelin sohbet şablonuna göre tek bir prompt'a çevirir."""
        dicts = [{"role": m.role, "content": m.content} for m in messages]
        if getattr(self._tokenizer, "chat_template", None):
            prompt: str = self._tokenizer.apply_chat_template(
                dicts, add_generation_prompt=True, tokenize=False
            )
            return prompt
        return "\n".join(f"{m.role}: {m.content}" for m in messages) + "\nassistant:"

    @staticmethod
    def _clean_output(text: str) -> str:
        """Çıktıya sızan özel token'ları (ör. ``<|end|>``) ve sonrasını kırpar."""
        idx = text.find("<|")
        if idx != -1:
            text = text[:idx]
        return text.strip()

    # ── Senkron çıkarım (thread'de çalıştırılır) ──

    def _generate_sync(self, prompt: str) -> str:
        """Tam yanıtı senkron üretir (``asyncio.to_thread`` içinde çağrılır)."""
        from mlx_lm import generate

        text: str = generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=self.max_tokens,
            verbose=False,
        )
        return text

    # ── LLMClient arayüzü ──

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        """Mesajları MLX modeline gönderir ve tam yanıtı döndürür.

        Args:
            messages: Sıralı sohbet mesajları.
            model: Yoksayılır (MLXClient tek modele bağlıdır); arayüz uyumu için.
            stream: ``True`` ise yanıt akışla toplanır, yine tam metin döner.

        Returns:
            Modelin yanıtını içeren :class:`ChatResponse`.
        """
        if stream:
            return await self._chat_collected(messages)

        await asyncio.to_thread(self._ensure_loaded)
        prompt = self._build_prompt(messages)

        start = time.perf_counter()
        raw = await asyncio.to_thread(self._generate_sync, prompt)
        latency_ms = (time.perf_counter() - start) * 1000

        content = self._clean_output(raw)
        tokens = len(self._tokenizer.encode(content)) if self._tokenizer else None
        logger.info(
            "MLX yanıt: model=%s, latency=%.0fms, tokens=%s",
            self.model_name,
            latency_ms,
            tokens,
        )
        return ChatResponse(
            content=content,
            model=self.model_name,
            latency_ms=latency_ms,
            tokens=tokens,
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """MLX yanıtını parça parça akış olarak verir.

        Senkron ``stream_generate`` bir worker thread'inde çalışır; üretilen
        parçalar bir :class:`asyncio.Queue` üzerinden async tarafa aktarılır.

        Args:
            messages: Sıralı sohbet mesajları.
            model: Yoksayılır; arayüz uyumu için.

        Yields:
            Yanıtın art arda gelen metin parçaları.
        """
        await asyncio.to_thread(self._ensure_loaded)
        prompt = self._build_prompt(messages)

        queue: asyncio.Queue[str | None] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def worker() -> None:
            from mlx_lm import stream_generate

            try:
                for resp in stream_generate(
                    self._model,
                    self._tokenizer,
                    prompt,
                    max_tokens=self.max_tokens,
                ):
                    loop.call_soon_threadsafe(queue.put_nowait, resp.text)
            except Exception:  # noqa: BLE001 — hata sentinel ile kapatılır
                logger.exception("MLX stream hatası")
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        threading.Thread(target=worker, daemon=True).start()

        while True:
            piece = await queue.get()
            if piece is None:
                break
            if not piece:
                continue
            # Özel token sızarsa öncesini ver ve akışı bitir.
            if "<|" in piece:
                head = piece[: piece.find("<|")]
                if head:
                    yield head
                break
            yield piece

    async def _chat_collected(self, messages: list[ChatMessage]) -> ChatResponse:
        """Akışı toplayıp tek :class:`ChatResponse` olarak döndürür."""
        start = time.perf_counter()
        parts: list[str] = []
        async for piece in self.chat_stream(messages):
            parts.append(piece)
        latency_ms = (time.perf_counter() - start) * 1000
        return ChatResponse(
            content="".join(parts).strip(),
            model=self.model_name,
            latency_ms=latency_ms,
            tokens=None,
        )

    async def list_models(self) -> list[str]:
        """Bu client'ın bağlı olduğu tek modelin adını döndürür."""
        return [self.model_name]

    async def health_check(self) -> bool:
        """MLX'in kullanılabilir olup olmadığını (import edilebilirliğini) döndürür.

        Returns:
            ``mlx_lm`` import edilebiliyorsa ``True``.
        """
        return importlib.util.find_spec("mlx_lm") is not None
