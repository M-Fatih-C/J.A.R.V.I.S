"""Sağlık kontrolü endpoint'i — servis ve alt sistem durumları."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from jarvis.api.dependencies import (
    get_mlx_client,
    get_ollama_client,
    get_short_term_memory,
)
from jarvis.memory import ShortTermMemory
from jarvis.models import MLXClient, OllamaClient

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """`/health` yanıtı — servis ve alt sistem durumları."""

    status: str
    ollama: bool
    mlx: bool
    redis: bool


@router.get("/health", response_model=HealthResponse)
async def health(
    ollama: Annotated[OllamaClient, Depends(get_ollama_client)],
    mlx: Annotated[MLXClient, Depends(get_mlx_client)],
    short_term: Annotated[ShortTermMemory, Depends(get_short_term_memory)],
) -> HealthResponse:
    """Servisin ve alt sistemlerin (Ollama, MLX, Redis) durumunu döndürür.

    Returns:
        Genel durum ve her alt sistemin erişilebilirliği.
    """
    return HealthResponse(
        status="ok",
        ollama=await ollama.health_check(),
        mlx=await mlx.health_check(),
        redis=await short_term.ping(),
    )
