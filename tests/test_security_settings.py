import pytest
from pydantic import ValidationError

from jarvis.config.settings import Settings


def test_default_server_is_loopback(monkeypatch):
    for key in ("HOST", "ENV"):
        monkeypatch.delenv(key, raising=False)
    assert Settings(_env_file=None).host == "127.0.0.1"


def test_production_rejects_example_secrets():
    with pytest.raises(ValidationError, match="Production mode requires a unique"):
        Settings(
            _env_file=None,
            env="prod",
            jwt_secret="change-me",
            device_key="change-me",
            sqlite_encryption_key="change-me",
        )


def test_production_rejects_disabled_authentication():
    with pytest.raises(ValidationError, match="requires authentication"):
        Settings(_env_file=None, env="prod", auth_enabled=False)


def test_production_accepts_explicit_non_default_keys():
    settings = Settings(
        _env_file=None,
        env="prod",
        jwt_secret="j" * 40,
        device_key="d" * 40,
        sqlite_encryption_key="e" * 40,
    )
    assert settings.auth_enabled
