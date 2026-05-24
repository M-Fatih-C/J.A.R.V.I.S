"""Jarvis FastAPI uygulaması — giriş noktası."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jarvis import __version__
from jarvis.api.dependencies import get_ollama_client
from jarvis.api.routes import chat, health
from jarvis.config import settings

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("jarvis.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Uygulama başlangıç/kapanış olayları.

    Başlangıçta Ollama erişilebilirliğini kontrol eder ve loglar.
    """
    client = get_ollama_client()
    ollama_ok = await client.health_check()
    if ollama_ok:
        logger.info("Ollama bağlantısı hazır: %s", settings.ollama_url)
    else:
        logger.warning(
            "Ollama'ya ulaşılamadı (%s). /chat istekleri başarısız olabilir.",
            settings.ollama_url,
        )
    yield
    logger.info("Jarvis API kapatılıyor.")


app = FastAPI(
    title="Jarvis API",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.env == "dev" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)


def main() -> None:
    """uvicorn ile geliştirme sunucusunu başlatır."""
    uvicorn.run(
        "jarvis.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
