"""Kimlik doğrulama endpoint'i — cihaz anahtarı karşılığı JWT verir."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from jarvis.api.auth import create_access_token
from jarvis.config import settings

router = APIRouter(tags=["auth"])


class TokenRequest(BaseModel):
    """`/auth/token` istek gövdesi."""

    device_key: str


class TokenResponse(BaseModel):
    """`/auth/token` yanıtı."""

    access_token: str
    token_type: str = "bearer"


@router.post("/auth/token", response_model=TokenResponse)
async def issue_token(request: TokenRequest) -> TokenResponse:
    """Geçerli cihaz anahtarı karşılığında bir erişim token'ı verir.

    Args:
        request: Cihaz anahtarını içeren istek.

    Returns:
        Bearer JWT.

    Raises:
        HTTPException: Cihaz anahtarı yanlışsa (401).
    """
    if not secrets.compare_digest(
        request.device_key.encode("utf-8"), settings.device_key.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz cihaz anahtarı"
        )
    return TokenResponse(access_token=create_access_token("device"))
