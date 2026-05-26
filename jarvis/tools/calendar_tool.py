"""Takvim araçları (iskelet) — etkinlik listele/oluştur.

Backend (Google/CalDAV) henüz bağlanmadı: ilgili callable verilmezse araç
"yapılandırılmamış" döner. Backend, async callable olarak enjekte edilir;
böylece modül belirli bir sağlayıcıdan bağımsız kalır.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field

from jarvis.tools.base import Tool

logger = logging.getLogger(__name__)


class CalendarEvent(BaseModel):
    """Bir takvim etkinliği."""

    title: str
    start: str = Field(description="ISO 8601 başlangıç zamanı")
    end: str | None = Field(default=None, description="ISO 8601 bitiş zamanı")
    description: str = ""


# Etkinlik oluşturur -> oluşturulan etkinliğin kimliği/özeti
CreateFn = Callable[[CalendarEvent], Awaitable[str]]
# Bir tarih/aralık ifadesi alır -> etkinlik listesi
ListFn = Callable[[str], Awaitable[list[CalendarEvent]]]


class CreateEventArgs(BaseModel):
    title: str = Field(description="Etkinlik başlığı")
    start: str = Field(description="ISO 8601 başlangıç zamanı (ör. 2026-05-27T10:00)")
    end: str | None = Field(default=None, description="ISO 8601 bitiş zamanı")
    description: str = Field(default="", description="Etkinlik açıklaması")


class ListEventsArgs(BaseModel):
    when: str = Field(default="today", description="Aralık ifadesi (ör. 'today', 'this week')")


class CreateEventTool(Tool):
    """Takvime yeni bir etkinlik ekler (backend yapılandırılmışsa)."""

    name = "create_calendar_event"
    description = "Takvime başlık, başlangıç/bitiş zamanıyla yeni bir etkinlik ekler."
    args_schema = CreateEventArgs

    def __init__(self, create_fn: CreateFn | None = None) -> None:
        """CreateEventTool'u başlatır.

        Args:
            create_fn: Etkinlik oluşturan async fonksiyon; ``None`` ise
                yapılandırılmamış sayılır.
        """
        self._create_fn = create_fn

    async def run(self, **kwargs: Any) -> str:
        args = CreateEventArgs(**kwargs)
        if self._create_fn is None:
            return "Takvim yapılandırılmamış (Google/CalDAV bağlantısı gerekli)."
        event = CalendarEvent(**args.model_dump())
        try:
            return await self._create_fn(event)
        except Exception as exc:  # noqa: BLE001 — dış servis hatasını modele bildir
            logger.warning("Etkinlik oluşturulamadı: %s", exc)
            return f"Hata: etkinlik oluşturulamadı: {exc}"


class ListEventsTool(Tool):
    """Takvimdeki etkinlikleri listeler (backend yapılandırılmışsa)."""

    name = "list_calendar_events"
    description = "Belirtilen aralıktaki takvim etkinliklerini listeler."
    args_schema = ListEventsArgs

    def __init__(self, list_fn: ListFn | None = None) -> None:
        """ListEventsTool'u başlatır.

        Args:
            list_fn: Etkinlikleri getiren async fonksiyon; ``None`` ise
                yapılandırılmamış sayılır.
        """
        self._list_fn = list_fn

    async def run(self, **kwargs: Any) -> str:
        args = ListEventsArgs(**kwargs)
        if self._list_fn is None:
            return "Takvim yapılandırılmamış (Google/CalDAV bağlantısı gerekli)."
        try:
            events = await self._list_fn(args.when)
        except Exception as exc:  # noqa: BLE001 — dış servis hatasını modele bildir
            logger.warning("Etkinlikler getirilemedi: %s", exc)
            return f"Hata: etkinlikler getirilemedi: {exc}"
        if not events:
            return "Bu aralıkta etkinlik yok."
        return "\n".join(f"- {e.title} ({e.start})" for e in events)
