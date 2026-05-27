"""JWT auth testleri — token üretimi/çözümü + /auth/token + uç nokta koruması."""

from __future__ import annotations

from collections.abc import Iterator

import jwt
import pytest
from fastapi.testclient import TestClient

from jarvis.api import auth as auth_mod
from jarvis.api.auth import create_access_token, decode_token
from jarvis.api.main import app
from jarvis.config import settings


def test_token_roundtrip() -> None:
    token = create_access_token("device")
    assert decode_token(token) == "device"


def test_decode_invalid_raises() -> None:
    with pytest.raises(jwt.PyJWTError):
        decode_token("açıkça.geçersiz.token")


@pytest.fixture
def client() -> Iterator[TestClient]:
    yield TestClient(app)


def test_issue_token_with_correct_key(client: TestClient) -> None:
    resp = client.post("/auth/token", json={"device_key": settings.device_key})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert decode_token(body["access_token"]) == "device"


def test_issue_token_wrong_key(client: TestClient) -> None:
    resp = client.post("/auth/token", json={"device_key": "yanlış"})
    assert resp.status_code == 401


def test_protected_endpoint_rejects_without_token(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(auth_mod.settings, "auth_enabled", True)
    resp = client.post("/chat", json={"message": "merhaba"})
    assert resp.status_code == 401


def test_protected_endpoint_rejects_bad_token(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(auth_mod.settings, "auth_enabled", True)
    resp = client.post(
        "/chat",
        json={"message": "merhaba"},
        headers={"Authorization": "Bearer bad-token-xyz"},
    )
    assert resp.status_code == 401


def test_health_is_public(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
