"""Merkezî uygulama ayarları (pydantic-settings, .env'den okur)."""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator
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
    host: str = "127.0.0.1"
    port: int = 8000

    # ── Ollama ──
    ollama_url: str = "http://localhost:11434"
    ollama_default_model: str = "qwen2.5:14b"
    ollama_embed_model: str = "nomic-embed-text"

    # ── Agent ──
    agent_workdir: str = "./data/workspace"

    # ── Voice ──
    stt_model: str = "mlx-community/whisper-large-v3-turbo"
    tts_voice: str = "Yelda"  # macOS 'say' Türkçe sesi
    wake_word: str = "hey_jarvis"
    wake_threshold: float = 0.5

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── ChromaDB ──
    chroma_path: str = "./data/chroma"

    # ── SQLite ──
    sqlite_path: str = "./data/jarvis.db"
    sqlite_encryption_key: str = "change-me"

    # ── Security ──
    jwt_secret: str = "change-me-please-to-a-32+byte-random-secret"
    jwt_algorithm: str = "HS256"
    auth_enabled: bool = True
    device_key: str = "change-me-device-key"  # cihazların token almak için sunduğu sır
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 gün

    @model_validator(mode="after")
    def require_production_secrets(self) -> Settings:
        if self.env == "prod":
            if not self.auth_enabled:
                raise ValueError("Production mode requires authentication")
            for name in ("jwt_secret", "device_key", "sqlite_encryption_key"):
                value = getattr(self, name)
                if len(value) < 32 or value.startswith("change-me"):
                    raise ValueError(
                        f"Production mode requires a unique {name} of at least 32 characters"
                    )
        return self


settings = Settings()
"""Uygulama genelinde kullanılan singleton ayar nesnesi."""
