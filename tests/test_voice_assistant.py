"""Ses-orchestrator wiring testleri (orchestrator + STT/TTS/wake mock'lu)."""

from __future__ import annotations

import numpy as np

from jarvis.core import Lane
from jarvis.core.orchestrator import ChatResult
from jarvis.voice.assistant import build_voice_pipeline, orchestrator_handler
from jarvis.voice.pipeline import VoicePipeline
from jarvis.voice.stt import STT
from jarvis.voice.tts import TTS


class FakeOrchestrator:
    """handle() çağrılarını kaydeden sahte orchestrator."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def handle(self, message: str, session_id: str = "default") -> ChatResult:
        self.calls.append((message, session_id))
        return ChatResult(
            content=f"yanıt: {message}",
            model="fake",
            lane=Lane.FAST,
            reason="test",
            latency_ms=1.0,
        )


class FakeSTT(STT):
    def __init__(self, text: str) -> None:
        self.text = text

    async def transcribe(self, audio: str | np.ndarray, language: str = "tr") -> str:
        return self.text


class FakeTTS(TTS):
    def __init__(self) -> None:
        self.spoken: list[str] = []

    async def synthesize(self, text: str, out_path: str) -> str:
        return out_path

    async def speak(self, text: str) -> None:
        self.spoken.append(text)


async def test_orchestrator_handler_returns_content() -> None:
    orch = FakeOrchestrator()
    handler = orchestrator_handler(orch, session_id="voice")
    reply = await handler("merhaba")
    assert reply == "yanıt: merhaba"
    assert orch.calls == [("merhaba", "voice")]


def test_build_voice_pipeline_wires_components() -> None:
    pipe = build_voice_pipeline(FakeOrchestrator(), stt=FakeSTT("x"), tts=FakeTTS(), wake=None)
    assert isinstance(pipe, VoicePipeline)


async def test_pipeline_routes_voice_through_orchestrator() -> None:
    orch = FakeOrchestrator()
    tts = FakeTTS()
    pipe = build_voice_pipeline(orch, stt=FakeSTT("bugün hava nasıl"), tts=tts)
    reply = await pipe.process_utterance("ses.wav")
    assert reply == "yanıt: bugün hava nasıl"
    assert orch.calls[0] == ("bugün hava nasıl", "voice")
    assert tts.spoken == ["yanıt: bugün hava nasıl"]
