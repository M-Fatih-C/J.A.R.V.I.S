"""Araştırma aracı — bir web sayfasının metin içeriğini getirir.

Çok adımlı araştırmayı agent yürütür (önce ``web_search``, sonra ilgili
bağlantılar için ``fetch_url``). Bu modül tekil sayfa getirme yeteneğini sağlar.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from pydantic import BaseModel, Field

from jarvis.tools.base import Tool

logger = logging.getLogger(__name__)

DEFAULT_MAX_CHARS = 5_000
DEFAULT_TIMEOUT = 15.0

# url -> ham HTML/metin
FetchFn = Callable[[str], Awaitable[str]]

_SCRIPT_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


async def _httpx_fetch(url: str) -> str:
    """Bir URL'yi httpx ile çeker ve gövdeyi metin olarak döndürür."""
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "JarvisBot/0.1"})
        resp.raise_for_status()
        return resp.text


def _html_to_text(html: str) -> str:
    """Basit HTML→metin: script/style at, etiketleri kaldır, boşlukları sıkıştır."""
    text = _SCRIPT_STYLE.sub(" ", html)
    text = _TAG.sub(" ", text)
    return _WS.sub(" ", text).strip()


class FetchUrlArgs(BaseModel):
    url: str = Field(description="İçeriği getirilecek sayfanın URL'si")


class FetchUrlTool(Tool):
    """Bir web sayfasını getirir ve okunabilir metin içeriğini döndürür."""

    name = "fetch_url"
    description = (
        "Verilen URL'deki web sayfasının metin içeriğini getirir. Bir kaynağı "
        "okuyup detaylı bilgi çıkarmak için kullanılır."
    )
    args_schema = FetchUrlArgs

    def __init__(self, fetch_fn: FetchFn | None = None, max_chars: int = DEFAULT_MAX_CHARS) -> None:
        """FetchUrlTool'u başlatır.

        Args:
            fetch_fn: Sayfa getirme fonksiyonu (test için enjekte edilebilir);
                ``None`` ise httpx kullanılır.
            max_chars: Döndürülecek azami karakter sayısı.
        """
        self._fetch_fn = fetch_fn or _httpx_fetch
        self.max_chars = max_chars

    async def run(self, **kwargs: Any) -> str:
        args = FetchUrlArgs(**kwargs)
        try:
            html = await self._fetch_fn(args.url)
        except Exception as exc:  # noqa: BLE001 — dış servis hatasını modele bildir
            logger.warning("Sayfa getirilemedi (%s): %s", args.url, exc)
            return f"Hata: sayfa getirilemedi: {exc}"

        text = _html_to_text(html)
        if len(text) > self.max_chars:
            return text[: self.max_chars] + "\n... (kırpıldı)"
        return text or "(boş içerik)"
