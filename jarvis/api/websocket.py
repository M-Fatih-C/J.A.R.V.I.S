"""WebSocket endpoint — Holo UI ile gerçek zamanlı sohbet.

İstemci JSON gönderir: ``{"message": "...", "session_id": "..."}``.
Sunucu sırayla event yayınlar:
    {"type": "status", "state": "thinking"}
    {"type": "response", "content": ..., "lane": ..., "model": ..., "latency_ms": ...}
    {"type": "status", "state": "idle"}
Hata olursa: {"type": "error", "detail": ...}
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from jarvis.api.dependencies import get_orchestrator
from jarvis.core import Orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
) -> None:
    """Holo UI için gerçek zamanlı sohbet WebSocket'i.

    Args:
        websocket: İstemci bağlantısı.
        orchestrator: Enjekte edilen Orchestrator (beyin).
    """
    await websocket.accept()
    logger.info("WS bağlantısı açıldı.")
    try:
        while True:
            data = await websocket.receive_json()
            message = (data.get("message") or "").strip()
            session_id = data.get("session_id") or "ui"
            if not message:
                await websocket.send_json({"type": "error", "detail": "boş mesaj"})
                continue

            await websocket.send_json({"type": "status", "state": "thinking"})
            try:
                result = await orchestrator.handle(message, session_id=session_id)
            except Exception as exc:  # noqa: BLE001 — hatayı istemciye bildir
                logger.warning("WS işleme hatası: %s", exc)
                await websocket.send_json({"type": "error", "detail": str(exc)})
            else:
                await websocket.send_json(
                    {
                        "type": "response",
                        "content": result.content,
                        "lane": result.lane.value,
                        "model": result.model,
                        "latency_ms": result.latency_ms,
                    }
                )
            await websocket.send_json({"type": "status", "state": "idle"})
    except WebSocketDisconnect:
        logger.info("WS bağlantısı kapandı.")
