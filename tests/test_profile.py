"""UserProfile + Cipher için testler (geçici SQLite dosyasıyla)."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.memory.profile import Cipher, UserProfile


@pytest.fixture
async def profile(tmp_path: Path) -> UserProfile:
    """Geçici dosyada başlatılmış bir UserProfile."""
    p = UserProfile(db_path=str(tmp_path / "test.db"), encryption_key="test-secret")
    await p.init_db()
    yield p
    await p.close()


# ── Cipher ──


def test_cipher_roundtrip() -> None:
    cipher = Cipher("parola")
    token = cipher.encrypt("gizli veri")
    assert token != "gizli veri"
    assert cipher.decrypt(token) == "gizli veri"


def test_cipher_nonce_is_random() -> None:
    cipher = Cipher("parola")
    assert cipher.encrypt("ayni") != cipher.encrypt("ayni")


def test_cipher_wrong_key_fails() -> None:
    token = Cipher("dogru").encrypt("veri")
    with pytest.raises(Exception):  # noqa: B017 — InvalidTag bekleniyor
        Cipher("yanlis").decrypt(token)


# ── UserProfile ──


async def test_set_and_get(profile: UserProfile) -> None:
    await profile.set("isim", "Fatih")
    assert await profile.get("isim") == "Fatih"


async def test_get_missing_returns_none(profile: UserProfile) -> None:
    assert await profile.get("yok") is None


async def test_set_overwrites(profile: UserProfile) -> None:
    await profile.set("sehir", "İstanbul")
    await profile.set("sehir", "Ankara")
    assert await profile.get("sehir") == "Ankara"


async def test_encrypted_value_stored_ciphered(profile: UserProfile, tmp_path: Path) -> None:
    await profile.set("api_key", "süper-gizli", encrypt=True)
    # Ham DB içeriğinde düz metin görünmemeli.
    db_bytes = (tmp_path / "test.db").read_bytes()
    assert b"s\xc3\xbcper-gizli" not in db_bytes
    assert await profile.get("api_key") == "süper-gizli"


async def test_plaintext_value(profile: UserProfile) -> None:
    await profile.set("dil", "tr", encrypt=False)
    assert await profile.get("dil") == "tr"


async def test_all_returns_decrypted(profile: UserProfile) -> None:
    await profile.set("a", "1", encrypt=True)
    await profile.set("b", "2", encrypt=False)
    assert await profile.all() == {"a": "1", "b": "2"}


async def test_delete(profile: UserProfile) -> None:
    await profile.set("gec", "ici")
    await profile.delete("gec")
    assert await profile.get("gec") is None


async def test_persists_across_instances(tmp_path: Path) -> None:
    path = str(tmp_path / "persist.db")
    p1 = UserProfile(db_path=path, encryption_key="k")
    await p1.init_db()
    await p1.set("kalici", "deger")
    await p1.close()

    p2 = UserProfile(db_path=path, encryption_key="k")
    await p2.init_db()
    assert await p2.get("kalici") == "deger"
    await p2.close()
