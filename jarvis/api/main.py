"""Jarvis FastAPI uygulaması — giriş noktası."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from jarvis import __version__
from jarvis import metrics as metrics_mod
from jarvis.api import websocket
from jarvis.api.dependencies import get_ollama_client
from jarvis.api.routes import agent, auth, chat, health
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


@app.middleware("http")
async def observability_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Her isteğe X-Request-ID atar, süreyi loglar ve Prometheus'a kaydeder."""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start

    path = request.url.path
    method = request.method
    metrics_mod.LATENCY.labels(method, path).observe(elapsed)
    metrics_mod.REQUESTS.labels(method, path, response.status_code).inc()
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s -> %s (%.0fms) [%s]",
        method,
        path,
        response.status_code,
        elapsed * 1000,
        request_id,
    )
    return response


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus metriklerini sunar."""
    return Response(metrics_mod.render(), media_type=metrics_mod.CONTENT_TYPE)


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(agent.router)
app.include_router(websocket.router)


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
