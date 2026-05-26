"""Agent endpoint'i — araç kullanabilen ReAct agent'ı çağırır."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from jarvis.api.dependencies import get_agent
from jarvis.core.agent import JarvisAgent

router = APIRouter(tags=["agent"])


class AgentRequest(BaseModel):
    """`/agent` istek gövdesi."""

    message: str


class AgentResponse(BaseModel):
    """`/agent` yanıtı."""

    content: str


@router.post("/agent", response_model=AgentResponse)
async def run_agent(
    request: AgentRequest,
    agent: Annotated[JarvisAgent, Depends(get_agent)],
) -> AgentResponse:
    """Çok adımlı, araç gerektiren bir isteği agent ile yürütür.

    Agent (Qwen 2.5) gerektiğinde dosya, shell, kod, web arama gibi araçları
    çağırarak görevi tamamlar.

    Args:
        request: Kullanıcı isteği.
        agent: Enjekte edilen JarvisAgent.

    Returns:
        Agent'ın ürettiği son yanıt.

    Raises:
        HTTPException: Agent çalışırken hata olursa (502).
    """
    try:
        content = await agent.run(request.message)
    except Exception as exc:  # noqa: BLE001 — agent/altyapı hatasını 502'ye çevir
        raise HTTPException(status_code=502, detail=f"Agent hatası: {exc}") from exc
    return AgentResponse(content=content)
