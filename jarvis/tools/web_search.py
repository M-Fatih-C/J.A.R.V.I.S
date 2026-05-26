"""Web arama aracı — anahtarsız DuckDuckGo (ddgs) üzerinden."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from jarvis.tools.base import Tool

logger = logging.getLogger(__name__)

DEFAULT_MAX_RESULTS = 5

# (query, max_results) -> sonuç sözlükleri listesi (title/href/body)
SearchFn = Callable[[str, int], list[dict[str, Any]]]


def _ddgs_search(query: str, max_results: int) -> list[dict[str, Any]]:
    """DuckDuckGo (ddgs) ile senkron metin araması yapar."""
    from ddgs import DDGS

    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


class WebSearchArgs(BaseModel):
    query: str = Field(description="Web'de aranacak sorgu")


class WebSearchTool(Tool):
    """DuckDuckGo üzerinden web araması yapar ve özet sonuçlar döndürür."""

    name = "web_search"
    description = (
        "Güncel bilgi için web'de arama yapar. Başlık, bağlantı ve kısa "
        "özetlerden oluşan sonuçlar döndürür."
    )
    args_schema = WebSearchArgs

    def __init__(
        self,
        search_fn: SearchFn | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
    ) -> None:
        """WebSearchTool'u başlatır.

        Args:
            search_fn: Arama fonksiyonu (test için enjekte edilebilir);
                ``None`` ise DuckDuckGo kullanılır.
            max_results: Döndürülecek azami sonuç sayısı.
        """
        self._search_fn = search_fn or _ddgs_search
        self.max_results = max_results

    async def run(self, **kwargs: Any) -> str:
        args = WebSearchArgs(**kwargs)
        try:
            results = await asyncio.to_thread(self._search_fn, args.query, self.max_results)
        except Exception as exc:  # noqa: BLE001 — dış servis hatasını modele bildir
            logger.warning("Web araması başarısız: %s", exc)
            return f"Hata: web araması başarısız: {exc}"

        if not results:
            return "Sonuç bulunamadı."

        lines: list[str] = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "(başlık yok)")
            href = r.get("href", "")
            body = r.get("body", "")
            lines.append(f"{i}. {title}\n   {href}\n   {body}")
        return "\n".join(lines)
