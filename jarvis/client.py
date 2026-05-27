"""Jarvis API için hafif senkron istemci SDK'sı.

Masaüstü/mobil istemciler (PyQt6, vb.) ve testler tarafından kullanılır.
Cihaz anahtarıyla token alır ve korunan uç noktalara Bearer ile erişir.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120.0


class JarvisClient:
    """Jarvis API'sine bağlanan senkron istemci.

    Attributes:
        base_url: API kök adresi (örn. ``http://mac.tail-scale.ts.net:8000``).
        token: Geçerli erişim token'ı (auth sonrası).
    """

    def __init__(
        self,
        base_url: str,
        device_key: str | None = None,
        token: str | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """JarvisClient'ı başlatır.

        Args:
            base_url: API kök adresi.
            device_key: ``/auth/token`` için cihaz anahtarı.
            token: Önceden alınmış token (varsa).
            transport: httpx taşıma katmanı (test için enjekte edilebilir).
            timeout: İstek zaman aşımı (saniye).
        """
        self.base_url = base_url.rstrip("/")
        self._device_key = device_key
        self.token = token
        self._client = httpx.Client(base_url=self.base_url, transport=transport, timeout=timeout)

    def authenticate(self) -> str:
        """Cihaz anahtarıyla bir erişim token'ı alır ve saklar.

        Returns:
            Alınan token.

        Raises:
            RuntimeError: Cihaz anahtarı ayarlı değilse.
            httpx.HTTPStatusError: Kimlik doğrulama başarısızsa.
        """
        if not self._device_key:
            raise RuntimeError("device_key gerekli")
        resp = self._client.post("/auth/token", json={"device_key": self._device_key})
        resp.raise_for_status()
        self.token = str(resp.json()["access_token"])
        logger.info("Token alındı.")
        return self.token

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def chat(self, message: str, session_id: str = "client") -> dict[str, Any]:
        """Bir sohbet mesajı gönderir.

        Token yoksa ve cihaz anahtarı varsa otomatik kimlik doğrular.

        Args:
            message: Kullanıcı mesajı.
            session_id: Oturum kimliği.

        Returns:
            Sunucunun JSON yanıtı (content, lane, model, ...).

        Raises:
            httpx.HTTPStatusError: İstek başarısızsa.
        """
        if not self.token and self._device_key:
            self.authenticate()
        resp = self._client.post(
            "/chat",
            json={"message": message, "session_id": session_id},
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return dict(resp.json())

    def health(self) -> dict[str, Any]:
        """Servis sağlık durumunu döndürür."""
        resp = self._client.get("/health")
        resp.raise_for_status()
        return dict(resp.json())

    def close(self) -> None:
        """HTTP istemcisini kapatır."""
        self._client.close()
