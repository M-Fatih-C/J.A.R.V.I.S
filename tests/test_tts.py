"""TTS testleri — macOS 'say' ile gerçek dosya üretimi (Mac'e bağlı)."""

from __future__ import annotations

import shutil
import wave
from pathlib import Path

import pytest

from jarvis.voice.tts import PiperTTS, SayTTS

_HAS_SAY = shutil.which("say") is not None
pytestmark = pytest.mark.skipif(not _HAS_SAY, reason="macOS 'say' bulunamadı.")


async def test_say_synthesize_creates_wav(tmp_path: Path) -> None:
    out = str(tmp_path / "selam.wav")
    result = await SayTTS().synthesize("merhaba efendim", out)
    assert result == out
    p = Path(out)
    assert p.exists() and p.stat().st_size > 0
    # Geçerli 16 kHz PCM WAV mı?
    with wave.open(out, "rb") as w:
        assert w.getframerate() == 16000
        assert w.getnframes() > 0


async def test_say_synthesize_aiff(tmp_path: Path) -> None:
    out = str(tmp_path / "selam.aiff")
    await SayTTS().synthesize("test", out)
    assert Path(out).stat().st_size > 0


async def test_piper_not_configured() -> None:
    with pytest.raises(RuntimeError, match="yapılandırılmamış"):
        await PiperTTS(model_path=None).synthesize("x", "/tmp/x.wav")
