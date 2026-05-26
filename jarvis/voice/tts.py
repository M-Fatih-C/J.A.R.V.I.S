"""Metin→konuşma (TTS) — macOS ``say`` (varsayılan) ve Piper (opsiyonel)."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "Yelda"  # macOS Türkçe sesi


class TTS(ABC):
    """Metin seslendirme arayüzü."""

    @abstractmethod
    async def synthesize(self, text: str, out_path: str) -> str:
        """Metni bir ses dosyasına yazar.

        Args:
            text: Seslendirilecek metin.
            out_path: Çıktı ses dosyası yolu.

        Returns:
            Yazılan dosyanın yolu.
        """
        raise NotImplementedError

    @abstractmethod
    async def speak(self, text: str) -> None:
        """Metni hoparlörden seslendirir.

        Args:
            text: Seslendirilecek metin.
        """
        raise NotImplementedError


class SayTTS(TTS):
    """macOS yerleşik ``say`` komutuyla TTS (sıfır bağımlılık).

    Attributes:
        voice: Kullanılacak ses (örn. Türkçe için ``Yelda``).
    """

    def __init__(self, voice: str = DEFAULT_VOICE) -> None:
        """SayTTS'i başlatır.

        Args:
            voice: macOS ``say`` ses adı.
        """
        self.voice = voice

    async def synthesize(self, text: str, out_path: str) -> str:
        """Metni ``say -o`` ile bir ses dosyasına yazar.

        ``.wav`` uzantısı 16 kHz PCM WAV üretir (STT için uygun); aksi halde
        varsayılan (AIFF) biçim kullanılır.
        """
        argv = ["say", "-v", self.voice]
        if out_path.endswith(".wav"):
            argv += ["--data-format=LEI16@16000"]
        argv += ["-o", out_path, "--", text]
        await self._run(argv)
        return out_path

    async def speak(self, text: str) -> None:
        """Metni hoparlörden seslendirir (``say``)."""
        await self._run(["say", "-v", self.voice, "--", text])

    @staticmethod
    async def _run(argv: list[str]) -> None:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"say başarısız: {stderr.decode('utf-8', 'replace')}")


class PiperTTS(TTS):
    """Piper nöral TTS (opsiyonel) — bir onnx ses modeli gerektirir.

    Model yolu verilmezse :meth:`synthesize`/:meth:`speak` hata döndürür.
    ``piper-tts`` paketi kurulu olmalıdır (varsayılan kurulumda yoktur).
    """

    def __init__(self, model_path: str | None = None) -> None:
        """PiperTTS'i başlatır.

        Args:
            model_path: Piper onnx ses modeli yolu; ``None`` ise yapılandırılmamış.
        """
        self.model_path = model_path

    async def synthesize(self, text: str, out_path: str) -> str:
        if self.model_path is None:
            raise RuntimeError("Piper modeli yapılandırılmamış (model_path gerekli).")
        from piper import PiperVoice  # lazy: piper-tts kurulu olmalı

        def _gen() -> None:
            voice = PiperVoice.load(self.model_path)
            with open(out_path, "wb") as f:
                voice.synthesize(text, f)

        await asyncio.to_thread(_gen)
        return out_path

    async def speak(self, text: str) -> None:
        raise NotImplementedError("PiperTTS.speak henüz desteklenmiyor; synthesize kullanın.")
