"""JWT kimlik doğrulama — cihaz anahtarı → token, HTTP & WS principal bağımlılıkları.

``settings.auth_enabled`` False ise tüm istekler "anonymous" olarak geçer
(yerel geliştirme). True ise korunan uç noktalar geçerli bir Bearer token
(HTTP) veya ``?token=`` (WebSocket) ister.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Query, WebSocketException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from jarvis.config import settings

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


def create_access_token(subject: str) -> str:
    """Verilen özne için süreli bir JWT üretir.

    Args:
        subject: Token sahibi (örn. ``device``).

    Returns:
        İmzalı JWT dizesi.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str:
    """JWT'yi doğrular ve özneyi (``sub``) döndürür.

    Args:
        token: İmzalı JWT.

    Returns:
        Token öznesi.

    Raises:
        jwt.PyJWTError: Token geçersiz veya süresi dolmuşsa.
    """
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return str(payload["sub"])


async def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    """HTTP isteklerini doğrular ve principal döndürür.

    Args:
        credentials: ``Authorization: Bearer <token>`` başlığı.

    Returns:
        Doğrulanmış principal (auth kapalıysa ``anonymous``).

    Raises:
        HTTPException: Auth açıkken token yok/geçersizse (401).
    """
    if not settings.auth_enabled:
        return "anonymous"
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token gerekli")
    try:
        return decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz token"
        ) from exc


async def get_ws_principal(token: Annotated[str | None, Query()] = None) -> str:
    """WebSocket bağlantılarını ``?token=`` sorgu parametresiyle doğrular.

    Args:
        token: Sorgu parametresindeki JWT.

    Returns:
        Doğrulanmış principal (auth kapalıysa ``anonymous``).

    Raises:
        WebSocketException: Auth açıkken token yok/geçersizse.
    """
    if not settings.auth_enabled:
        return "anonymous"
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    try:
        return decode_token(token)
    except jwt.PyJWTError as exc:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc
