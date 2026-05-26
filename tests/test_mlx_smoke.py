"""Gerçek MLX modeliyle yavaş smoke testi.

Varsayılan olarak atlanır (modeli yüklemek yavaş). Çalıştırmak için:
    JARVIS_MLX_SMOKE=1 uv run pytest tests/test_mlx_smoke.py -v
"""

from __future__ import annotations

import os

import pytest

from jarvis.models import ChatMessage, MLXClient

pytestmark = pytest.mark.skipif(
    os.environ.get("JARVIS_MLX_SMOKE") != "1",
    reason="Gerçek MLX smoke testi atlandı (JARVIS_MLX_SMOKE=1 ile etkinleşir).",
)


async def test_real_inference() -> None:
    client = MLXClient(max_tokens=32)
    assert client.is_loaded is False
    resp = await client.chat([ChatMessage(role="user", content="Merhaba, kısaca selam ver.")])
    assert client.is_loaded is True
    assert resp.content.strip()
    assert resp.tokens and resp.tokens > 0
    client.unload()
    assert client.is_loaded is False
