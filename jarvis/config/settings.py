"""Merkezî uygulama ayarları (pydantic-settings, .env'den okur)."""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Tüm Jarvis yapılandırması. Değerler ortam değişkenlerinden / .env'den gelir.

    Yeni bir ayar eklerken hem buraya hem de ``.env.example`` dosyasına ekleyin.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──
    app_name: str = "Jarvis"
    env: Literal["dev", "prod"] = "dev"
    debug: bool = True
    log_level: str = "INFO"

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Ollama ──
    ollama_url: str = "http://localhost:11434"
    ollama_default_model: str = "qwen2.5:14b"
    ollama_embed_model: str = "nomic-embed-text"

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── ChromaDB ──
    chroma_path: str = "./data/chroma"

    # ── SQLite ──
    sqlite_path: str = "./data/jarvis.db"
    sqlite_encryption_key: str = "change-me"

    # ── Security ──
    jwt_secret: str = "change-me-please"
    jwt_algorithm: str = "HS256"


settings = Settings()
"""Uygulama genelinde kullanılan singleton ayar nesnesi."""
