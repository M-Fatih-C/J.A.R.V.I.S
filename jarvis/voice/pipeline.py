"""Ses pipeline'ı — wake word → kayıt → STT → handler → TTS akışı.

Çekirdek (:meth:`process_utterance`) donanımsızdır ve birim test edilir.
Canlı mikrofon döngüsü (:meth:`run`) ``sounddevice``'i lazy import eder ve
gerçek mikrofon gerektirir (birim test edilmez).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import cast

import numpy as np

from jarvis.voice.stt import STT, WHISPER_SAMPLE_RATE
from jarvis.voice.tts import TTS
from jarvis.voice.wake_word import FRAME_SAMPLES, WakeWord

logger = logging.getLogger(__name__)

# Çözülen metni alıp yanıt üreten async fonksiyon (ör. orchestrator/agent).
Handler = Callable[[str], Awaitable[str]]

DEFAULT_UTTERANCE_SECONDS = 5.0


class VoicePipeline:
    """Sesli etkileşim akışını yöneten koordinatör."""

    def __init__(
        self,
        stt: STT,
        tts: TTS,
        handler: Handler,
        wake: WakeWord | None = None,
        utterance_seconds: float = DEFAULT_UTTERANCE_SECONDS,
    ) -> None:
        """VoicePipeline'ı başlatır.

        Args:
            stt: Konuşma→metin motoru.
            tts: Metin→konuşma motoru.
            handler: Metni alıp yanıt üreten async fonksiyon.
            wake: Wake word detektörü (canlı döngü için); ``None`` olabilir.
            utterance_seconds: Wake sonrası kaydedilecek süre (saniye).
        """
        self._stt = stt
        self._tts = tts
        self._handler = handler
        self._wake = wake
        self.utterance_seconds = utterance_seconds

    async def process_utterance(self, audio: str | np.ndarray) -> str:
        """Bir sesi çözer, handler'a verir ve yanıtı seslendirir.

        Args:
            audio: WAV yolu veya 16 kHz mono float32 dizi.

        Returns:
            Üretilen yanıt metni; ses boşsa boş dize.
        """
        text = await self._stt.transcribe(audio)
        if not text:
            logger.info("Boş transkripsiyon; atlanıyor.")
            return ""
        logger.info("Kullanıcı (ses): %s", text)
        reply = await self._handler(text)
        await self._tts.speak(reply)
        return reply

    async def run(self) -> None:  # pragma: no cover — canlı mikrofon gerektirir
        """Canlı döngü: wake word'ü dinler, konuşmayı kaydeder, işler.

        ``sounddevice`` lazy import edilir; gerçek mikrofon gerektirir.

        Raises:
            RuntimeError: Wake word detektörü yapılandırılmamışsa.
        """
        if self._wake is None:
            raise RuntimeError("Canlı döngü için wake word detektörü gerekli.")
        import sounddevice as sd

        logger.info("Jarvis dinliyor — 'Hey Jarvis' deyin.")
        with sd.InputStream(samplerate=WHISPER_SAMPLE_RATE, channels=1, dtype="int16") as stream:
            while True:
                frame, _ = stream.read(FRAME_SAMPLES)
                frame = frame.reshape(-1)
                if self._wake.detected(frame):
                    logger.info("Wake word algılandı.")
                    self._wake.reset()
                    audio = await self._record(stream)
                    await self.process_utterance(audio)

    async def _record(self, stream: object) -> np.ndarray:  # pragma: no cover
        """Wake sonrası sabit süre kayıt yapıp float32 dizi döndürür."""
        total = int(WHISPER_SAMPLE_RATE * self.utterance_seconds)
        data, _ = await asyncio.to_thread(stream.read, total)  # type: ignore[attr-defined]
        return cast("np.ndarray", data.reshape(-1).astype(np.float32) / 32768.0)
