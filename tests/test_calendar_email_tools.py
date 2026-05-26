"""calendar ve email iskelet araçları için testler."""

from __future__ import annotations

from jarvis.tools.calendar_tool import (
    CalendarEvent,
    CreateEventTool,
    ListEventsTool,
)
from jarvis.tools.email_tool import SendEmailTool

# ── email ──


async def test_email_not_configured() -> None:
    tool = SendEmailTool(send_fn=None)
    out = await tool.run(to="a@b.com", subject="selam", body="merhaba")
    assert "yapılandırılmamış" in out


async def test_email_sends_via_injected_fn() -> None:
    sent: dict[str, str] = {}

    def fake_send(to: str, subject: str, body: str) -> None:
        sent.update(to=to, subject=subject, body=body)

    tool = SendEmailTool(send_fn=fake_send)
    out = await tool.run(to="a@b.com", subject="selam", body="merhaba")
    assert "gönderildi" in out
    assert sent == {"to": "a@b.com", "subject": "selam", "body": "merhaba"}


async def test_email_handles_send_error() -> None:
    def boom(to: str, subject: str, body: str) -> None:
        raise RuntimeError("smtp down")

    out = await SendEmailTool(send_fn=boom).run(to="a@b.com", subject="x", body="y")
    assert "gönderilemedi" in out


# ── calendar ──


async def test_calendar_create_not_configured() -> None:
    out = await CreateEventTool(create_fn=None).run(title="Toplantı", start="2026-05-27T10:00")
    assert "yapılandırılmamış" in out


async def test_calendar_create_via_injected_fn() -> None:
    captured: dict[str, CalendarEvent] = {}

    async def fake_create(event: CalendarEvent) -> str:
        captured["e"] = event
        return f"oluşturuldu: {event.title}"

    out = await CreateEventTool(create_fn=fake_create).run(
        title="Toplantı", start="2026-05-27T10:00", description="ekip"
    )
    assert "oluşturuldu: Toplantı" in out
    assert captured["e"].description == "ekip"


async def test_calendar_list_not_configured() -> None:
    out = await ListEventsTool(list_fn=None).run(when="today")
    assert "yapılandırılmamış" in out


async def test_calendar_list_events() -> None:
    async def fake_list(when: str) -> list[CalendarEvent]:
        return [CalendarEvent(title="Spor", start="2026-05-27T18:00")]

    out = await ListEventsTool(list_fn=fake_list).run(when="today")
    assert "Spor" in out


async def test_calendar_list_empty() -> None:
    async def fake_list(when: str) -> list[CalendarEvent]:
        return []

    out = await ListEventsTool(list_fn=fake_list).run(when="today")
    assert "etkinlik yok" in out
