"""E-posta aracı (iskelet) — SMTP ile gönderim.

Kimlik bilgileri henüz bağlanmadı: ``send_fn`` verilmezse araç "yapılandırılmamış"
döner. Gerçek kullanım için :func:`make_smtp_sender` ile bir gönderici üretip
enjekte edin.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from collections.abc import Callable
from email.message import EmailMessage
from typing import Any

from pydantic import BaseModel, Field

from jarvis.tools.base import Tool

logger = logging.getLogger(__name__)

# (to, subject, body) -> gönderir
SendFn = Callable[[str, str, str], None]


class SmtpConfig(BaseModel):
    """SMTP bağlantı ayarları."""

    host: str
    port: int = 587
    username: str
    password: str
    from_addr: str
    use_tls: bool = True


def make_smtp_sender(config: SmtpConfig) -> SendFn:
    """SMTP ayarlarından senkron bir gönderici fonksiyon üretir.

    Args:
        config: SMTP bağlantı ayarları.

    Returns:
        ``(to, subject, body)`` alan ve e-postayı gönderen fonksiyon.
    """

    def _send(to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = config.from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(config.host, config.port) as server:
            if config.use_tls:
                server.starttls()
            server.login(config.username, config.password)
            server.send_message(msg)

    return _send


class SendEmailArgs(BaseModel):
    to: str = Field(description="Alıcının e-posta adresi")
    subject: str = Field(description="E-posta konusu")
    body: str = Field(description="E-posta gövdesi (düz metin)")


class SendEmailTool(Tool):
    """Bir e-posta gönderir (SMTP yapılandırılmışsa)."""

    name = "send_email"
    description = "Belirtilen alıcıya konu ve gövdeyle bir e-posta gönderir."
    args_schema = SendEmailArgs

    def __init__(self, send_fn: SendFn | None = None) -> None:
        """SendEmailTool'u başlatır.

        Args:
            send_fn: Gönderici fonksiyon; ``None`` ise araç yapılandırılmamış sayılır.
        """
        self._send_fn = send_fn

    async def run(self, **kwargs: Any) -> str:
        args = SendEmailArgs(**kwargs)
        if self._send_fn is None:
            return "E-posta yapılandırılmamış (SMTP kimlik bilgileri gerekli)."
        try:
            await asyncio.to_thread(self._send_fn, args.to, args.subject, args.body)
        except Exception as exc:  # noqa: BLE001 — dış servis hatasını modele bildir
            logger.warning("E-posta gönderilemedi: %s", exc)
            return f"Hata: e-posta gönderilemedi: {exc}"
        return f"E-posta gönderildi: {args.to}"
