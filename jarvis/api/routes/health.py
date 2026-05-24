"""Sağlık kontrolü endpoint'i."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from jarvis.api.dependencies import get_ollama_client
from jarvis.models import OllamaClient

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """`/health` yanıtı."""

    status: str
    ollama: bool


@router.get("/health", response_model=HealthResponse)
async def health(
    client: Annotated[OllamaClient, Depends(get_ollama_client)],
) -> HealthResponse:
    """Servisin ve Ollama bağlantısının durumunu döndürür.

    Returns:
        Genel durum ve Ollama erişilebilirliği.
    """
    ollama_ok = await client.health_check()
    return HealthResponse(status="ok", ollama=ollama_ok)
