#!/usr/bin/env python
"""Jarvis sesli asistanı — canlı "Hey Jarvis" döngüsü.

Mikrofon, Ollama (Deep Think için ``qwen2.5:14b``) ve ``[voice]`` extra'sı
gerektirir. "Hey Jarvis" deyince dinler, konuşmanızı yazıya çevirir,
Orchestrator ile yanıtlar ve sesli okur.

Kullanım:
    uv run --extra voice --extra mlx python scripts/voice.py
"""

from __future__ import annotations

import asyncio
import logging

from jarvis.config import settings
from jarvis.voice.assistant import build_voice_pipeline


async def main() -> None:
    logging.basicConfig(level=settings.log_level)
    # Orchestrator'ı burada (script bağlamında) kuruyoruz; API/agent bağımlılığı
    # çekmemek için voice katmanı ondan bağımsızdır.
    from jarvis.api.dependencies import get_orchestrator

    pipeline = build_voice_pipeline(get_orchestrator())
    print("🎙️  Jarvis hazır. 'Hey Jarvis' deyin (çıkış: Ctrl+C).")
    try:
        await pipeline.run()
    except KeyboardInterrupt:
        print("\nGörüşmek üzere efendim.")


if __name__ == "__main__":
    asyncio.run(main())
