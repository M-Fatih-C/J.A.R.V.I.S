"""Sohbet endpoint'i — mesajı Ollama'ya iletir."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from jarvis.api.dependencies import get_ollama_client
from jarvis.models import ChatMessage, ChatResponse, OllamaClient

router = APIRouter(tags=["chat"])

JARVIS_SYSTEM_PROMPT = (
    "Sen Jarvis'sin: sakin, kendinden emin, hafif İngiliz uşağı havasında bir "
    "kişisel asistan. Kullanıcıya 'efendim' diye hitap edersin. Kısa ve öz "
    "yanıt verirsin, gereksiz açıklama yapmazsın."
)


class ChatRequest(BaseModel):
    """`/chat` istek gövdesi."""

    message: str
    model: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    client: Annotated[OllamaClient, Depends(get_ollama_client)],
) -> ChatResponse:
    """Kullanıcı mesajını Ollama'ya gönderir ve yanıtı döndürür.

    Args:
        request: Kullanıcı mesajı ve isteğe bağlı model.
        client: Enjekte edilen Ollama client'ı.

    Returns:
        Modelin :class:`ChatResponse` yanıtı.

    Raises:
        HTTPException: Ollama'ya ulaşılamaz veya hata dönerse (502).
    """
    messages = [
        ChatMessage(role="system", content=JARVIS_SYSTEM_PROMPT),
        ChatMessage(role="user", content=request.message),
    ]
    try:
        return await client.chat(messages, model=request.model)
    except Exception as exc:  # noqa: BLE001 — dış servis hatasını 502'ye çeviriyoruz
        raise HTTPException(status_code=502, detail=f"Ollama hatası: {exc}") from exc
