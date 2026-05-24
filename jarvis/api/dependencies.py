"""FastAPI dependency injection sağlayıcıları."""

from __future__ import annotations

from functools import lru_cache

from jarvis.config import settings
from jarvis.models import OllamaClient


@lru_cache(maxsize=1)
def get_ollama_client() -> OllamaClient:
    """Tekil (singleton) :class:`OllamaClient` örneği döndürür.

    ``lru_cache`` sayesinde uygulama yaşam döngüsü boyunca aynı örnek
    yeniden kullanılır.

    Returns:
        Ayarlardan yapılandırılmış :class:`OllamaClient`.
    """
    return OllamaClient(
        base_url=settings.ollama_url,
        default_model=settings.ollama_default_model,
        embed_model=settings.ollama_embed_model,
    )
