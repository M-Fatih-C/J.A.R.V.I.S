"""Ses asistanı wiring'i — VoicePipeline'ı Orchestrator'a bağlar.

Orchestrator'ı handler olarak saran ince bir katman + tam pipeline'ı kuran
fabrika. API/langchain bağımlılığı çekmemek için Orchestrator dışarıdan verilir.
"""

from __future__ import annotations

from jarvis.config import settings
from jarvis.core.orchestrator import Orchestrator
from jarvis.voice.pipeline import Handler, VoicePipeline
from jarvis.voice.stt import STT, WhisperSTT
from jarvis.voice.tts import TTS, SayTTS
from jarvis.voice.wake_word import WakeWord


def orchestrator_handler(orchestrator: Orchestrator, session_id: str = "voice") -> Handler:
    """Orchestrator'ı (metin→metin) bir pipeline handler'ına dönüştürür.

    Args:
        orchestrator: Kullanılacak Orchestrator.
        session_id: Sesli konuşmalar için oturum kimliği.

    Returns:
        Çözülen metni alıp yanıt metni döndüren async handler.
    """

    async def handler(text: str) -> str:
        result = await orchestrator.handle(text, session_id=session_id)
        return result.content

    return handler


def build_voice_pipeline(
    orchestrator: Orchestrator,
    *,
    stt: STT | None = None,
    tts: TTS | None = None,
    wake: WakeWord | None = None,
) -> VoicePipeline:
    """Ayarlardan tam bir :class:`VoicePipeline` kurar.

    Args:
        orchestrator: Beyin (handler olarak sarılır).
        stt: STT motoru; ``None`` ise ayarlardan ``WhisperSTT``.
        tts: TTS motoru; ``None`` ise ayarlardan ``SayTTS``.
        wake: Wake word detektörü; ``None`` ise ayarlardan ``WakeWord``.

    Returns:
        Çalışmaya hazır :class:`VoicePipeline`.
    """
    stt = stt or WhisperSTT(settings.stt_model)
    tts = tts or SayTTS(settings.tts_voice)
    wake = wake or WakeWord(settings.wake_word, settings.wake_threshold)
    return VoicePipeline(stt, tts, orchestrator_handler(orchestrator), wake=wake)
