"""VoicePipeline çekirdek akışı testleri — STT/TTS/handler mock'lu."""

from __future__ import annotations

import numpy as np

from jarvis.voice.pipeline import VoicePipeline
from jarvis.voice.stt import STT
from jarvis.voice.tts import TTS


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


async def test_process_utterance_flow() -> None:
    stt = FakeSTT("merhaba jarvis")
    tts = FakeTTS()
    received: dict[str, str] = {}

    async def handler(text: str) -> str:
        received["text"] = text
        return "Buyurun efendim."

    pipe = VoicePipeline(stt, tts, handler)
    reply = await pipe.process_utterance("ses.wav")

    assert received["text"] == "merhaba jarvis"
    assert reply == "Buyurun efendim."
    assert tts.spoken == ["Buyurun efendim."]


async def test_empty_transcription_skips_handler() -> None:
    tts = FakeTTS()
    called = False

    async def handler(text: str) -> str:
        nonlocal called
        called = True
        return "x"

    pipe = VoicePipeline(FakeSTT(""), tts, handler)
    reply = await pipe.process_utterance("ses.wav")

    assert reply == ""
    assert called is False
    assert tts.spoken == []


async def test_accepts_ndarray_audio() -> None:
    tts = FakeTTS()

    async def handler(text: str) -> str:
        return "tamam"

    pipe = VoicePipeline(FakeSTT("test"), tts, handler)
    reply = await pipe.process_utterance(np.zeros(1600, dtype=np.float32))
    assert reply == "tamam"
