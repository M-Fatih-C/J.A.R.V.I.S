"""Sohbet endpoint'i — mesajı Orchestrator üzerinden işler."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from jarvis.api.dependencies import get_orchestrator
from jarvis.core import ChatResult, Orchestrator

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """`/chat` istek gövdesi."""

    message: str
    session_id: str = "default"


@router.post("/chat", response_model=ChatResult)
async def chat(
    request: ChatRequest,
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
) -> ChatResult:
    """Kullanıcı mesajını Orchestrator'a iletir ve yanıtı döndürür.

    Orchestrator niyete göre Fast Lane (MLX) veya Deep Think (Ollama) hattını
    seçer, kısa süreli hafızadan bağlamı ekler ve yanıtı üretir.

    Args:
        request: Kullanıcı mesajı ve oturum kimliği.
        orchestrator: Enjekte edilen Orchestrator.

    Returns:
        Yanıt ve yönlendirme bilgisini içeren :class:`ChatResult`.

    Raises:
        HTTPException: Seçilen model hattına ulaşılamazsa (502).
    """
    try:
        return await orchestrator.handle(request.message, session_id=request.session_id)
    except Exception as exc:  # noqa: BLE001 — model/altyapı hatasını 502'ye çevir
        raise HTTPException(status_code=502, detail=f"Model hatası: {exc}") from exc
