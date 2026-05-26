"""STT testleri — mlx_whisper mock'lu; gerçek round-trip JARVIS_VOICE=1 ile."""

from __future__ import annotations

import os
import wave
from pathlib import Path

import numpy as np
import pytest

from jarvis.voice.stt import WhisperSTT, load_wav


def _write_wav(path: Path, freq: int = 440, rate: int = 16000, secs: float = 0.2) -> None:
    t = np.linspace(0, secs, int(rate * secs), endpoint=False)
    samples = (0.3 * np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.tobytes())


def test_load_wav_returns_float32_mono(tmp_path: Path) -> None:
    p = tmp_path / "tone.wav"
    _write_wav(p)
    data = load_wav(str(p))
    assert data.dtype == np.float32
    assert data.ndim == 1
    assert data.size > 0
    assert float(np.max(np.abs(data))) <= 1.0


def test_load_wav_resamples(tmp_path: Path) -> None:
    p = tmp_path / "tone8k.wav"
    _write_wav(p, rate=8000, secs=0.5)
    data = load_wav(str(p))
    # 8 kHz, 0.5 sn → 16 kHz'de ~8000 örnek.
    assert abs(data.size - 8000) < 50


async def test_transcribe_uses_mlx_whisper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "x.wav"
    _write_wav(p)

    captured: dict[str, object] = {}

    class FakeMLX:
        @staticmethod
        def transcribe(audio: object, path_or_hf_repo: str, language: str) -> dict:
            captured["audio_type"] = type(audio).__name__
            captured["language"] = language
            return {"text": "  merhaba dünya  "}

    monkeypatch.setitem(__import__("sys").modules, "mlx_whisper", FakeMLX)

    text = await WhisperSTT(model="fake").transcribe(str(p), language="tr")
    assert text == "merhaba dünya"
    # WAV, ffmpeg'siz numpy dizisine yüklenip verilmeli.
    assert captured["audio_type"] == "ndarray"
    assert captured["language"] == "tr"


@pytest.mark.skipif(
    "JARVIS_VOICE" not in os.environ,
    reason="Gerçek STT testi atlandı (JARVIS_VOICE=1 ile etkinleşir).",
)
async def test_real_transcription(tmp_path: Path) -> None:
    """say ile üretilen WAV'ı gerçek mlx-whisper ile çözer."""
    from jarvis.voice.tts import SayTTS

    wav = str(tmp_path / "soyle.wav")
    await SayTTS().synthesize("merhaba dünya", wav)
    text = await WhisperSTT().transcribe(wav, language="tr")
    assert "merhaba" in text.lower()
