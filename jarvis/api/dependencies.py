"""FastAPI dependency injection sağlayıcıları."""

from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis

from jarvis.config import settings
from jarvis.core import Orchestrator, Router
from jarvis.memory import ShortTermMemory
from jarvis.models import MLXClient, OllamaClient


@lru_cache(maxsize=1)
def get_ollama_client() -> OllamaClient:
    """Tekil (singleton) :class:`OllamaClient` örneği döndürür (Deep Think).

    Returns:
        Ayarlardan yapılandırılmış :class:`OllamaClient`.
    """
    return OllamaClient(
        base_url=settings.ollama_url,
        default_model=settings.ollama_default_model,
        embed_model=settings.ollama_embed_model,
    )


@lru_cache(maxsize=1)
def get_mlx_client() -> MLXClient:
    """Tekil (singleton) :class:`MLXClient` örneği döndürür (Fast Lane).

    Model lazy yüklenir; bu çağrı modeli yüklemez.

    Returns:
        :class:`MLXClient` örneği.
    """
    return MLXClient()


@lru_cache(maxsize=1)
def get_router() -> Router:
    """Tekil (singleton) :class:`Router` örneği döndürür."""
    return Router()


@lru_cache(maxsize=1)
def get_short_term_memory() -> ShortTermMemory:
    """Tekil (singleton) :class:`ShortTermMemory` döndürür.

    Redis bağlantısı tembeldir (ilk komutta kurulur); Redis çalışmıyorsa
    Orchestrator durumsuz olarak devam eder.

    Returns:
        Ayarlardan yapılandırılmış :class:`ShortTermMemory`.
    """
    redis: Redis = Redis.from_url(settings.redis_url)
    return ShortTermMemory(redis)


@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:
    """Router, model client'ları ve hafızayı birleştiren :class:`Orchestrator`.

    Returns:
        Yapılandırılmış :class:`Orchestrator` örneği.
    """
    return Orchestrator(
        router=get_router(),
        fast_client=get_mlx_client(),
        deep_client=get_ollama_client(),
        short_term=get_short_term_memory(),
    )
