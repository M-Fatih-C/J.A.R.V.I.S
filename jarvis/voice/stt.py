"""Konuşma→metin (STT) — mlx-whisper (Apple Silicon).

WAV girdileri stdlib ``wave`` ile numpy dizisine yüklenir; böylece yaygın
durumda ffmpeg gerekmez. Diğer biçimler doğrudan mlx-whisper'a verilir
(mlx-whisper kendi çözümleyicisini/ffmpeg'i kullanabilir).
"""

from __future__ import annotations

import asyncio
import logging
import wave
from abc import ABC, abstractmethod

import numpy as np

logger = logging.getLogger(__name__)

WHISPER_SAMPLE_RATE = 16_000
DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"


def load_wav(path: str) -> np.ndarray:
    """Bir PCM16 WAV dosyasını 16 kHz mono float32 diziye yükler.

    Args:
        path: WAV dosya yolu.

    Returns:
        [-1, 1] aralığında, 16 kHz, mono ``float32`` dizi.
    """
    with wave.open(path, "rb") as w:
        channels = w.getnchannels()
        rate = w.getframerate()
        frames = w.readframes(w.getnframes())

    data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    if rate != WHISPER_SAMPLE_RATE and data.size:
        # Basit doğrusal yeniden örnekleme.
        target_len = int(round(data.size * WHISPER_SAMPLE_RATE / rate))
        data = np.interp(
            np.linspace(0, data.size, target_len, endpoint=False),
            np.arange(data.size),
            data,
        ).astype(np.float32)
    return data


class STT(ABC):
    """Konuşma tanıma arayüzü."""

    @abstractmethod
    async def transcribe(self, audio: str | np.ndarray, language: str = "tr") -> str:
        """Sesi metne çevirir.

        Args:
            audio: WAV dosya yolu veya 16 kHz mono float32 dizi.
            language: Beklenen dil kodu (örn. ``tr``).

        Returns:
            Çözülen metin.
        """
        raise NotImplementedError


class WhisperSTT(STT):
    """mlx-whisper ile konuşma tanıma.

    Attributes:
        model: HuggingFace MLX Whisper model deposu.
    """

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        """WhisperSTT'i başlatır.

        Args:
            model: Kullanılacak MLX Whisper modeli.
        """
        self.model = model

    async def transcribe(self, audio: str | np.ndarray, language: str = "tr") -> str:
        if isinstance(audio, str) and audio.lower().endswith(".wav"):
            audio_input: str | np.ndarray = load_wav(audio)
        else:
            audio_input = audio

        def _run() -> str:
            import mlx_whisper

            result = mlx_whisper.transcribe(
                audio_input, path_or_hf_repo=self.model, language=language
            )
            return str(result.get("text", "")).strip()

        text = await asyncio.to_thread(_run)
        logger.info("STT sonucu (%d karakter)", len(text))
        return text
