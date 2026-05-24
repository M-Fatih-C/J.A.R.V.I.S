"""Kullanıcı profili — async SQLite (SQLAlchemy) + alan bazında AES-256-GCM.

Hassas değerler diske yazılmadan önce AES-256-GCM ile şifrelenir. Şema açık
kalır (anahtarlar düz metin), yalnızca ``encrypt=True`` ile yazılan değerler
şifrelenir.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
from datetime import UTC, datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import Boolean, DateTime, String, delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

logger = logging.getLogger(__name__)

_NONCE_BYTES = 12


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Cipher:
    """AES-256-GCM ile metin şifreleme/çözme yardımcı sınıfı.

    Anahtar, verilen parolanın SHA-256 özetinden (32 bayt) türetilir.
    """

    def __init__(self, passphrase: str) -> None:
        """Cipher'ı bir paroladan başlatır.

        Args:
            passphrase: Şifreleme anahtarının türetileceği parola.
        """
        self._key = hashlib.sha256(passphrase.encode("utf-8")).digest()

    def encrypt(self, plaintext: str) -> str:
        """Metni şifreler.

        Args:
            plaintext: Şifrelenecek düz metin.

        Returns:
            base64(nonce + şifreli metin) biçiminde dize.
        """
        nonce = os.urandom(_NONCE_BYTES)
        ct = AESGCM(self._key).encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ct).decode("ascii")

    def decrypt(self, token: str) -> str:
        """Şifreli metni çözer.

        Args:
            token: :meth:`encrypt` çıktısı.

        Returns:
            Çözülmüş düz metin.
        """
        raw = base64.b64decode(token)
        nonce, ct = raw[:_NONCE_BYTES], raw[_NONCE_BYTES:]
        return AESGCM(self._key).decrypt(nonce, ct, None).decode("utf-8")


class Base(DeclarativeBase):
    """SQLAlchemy declarative taban."""


class ProfileEntry(Base):
    """Profil anahtar-değer kaydı."""

    __tablename__ = "profile"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class UserProfile:
    """SQLite tabanlı kullanıcı profili deposu (anahtar-değer).

    Attributes:
        db_path: SQLite dosya yolu.
    """

    def __init__(self, db_path: str, encryption_key: str) -> None:
        """UserProfile'ı başlatır.

        Args:
            db_path: SQLite dosya yolu (örn. ``./data/jarvis.db``).
            encryption_key: Hassas alanları şifrelemek için parola.
        """
        self.db_path = db_path
        self._engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        self._session = async_sessionmaker(self._engine, expire_on_commit=False)
        self._cipher = Cipher(encryption_key)

    async def init_db(self) -> None:
        """Tabloları (yoksa) oluşturur."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def set(self, key: str, value: str, encrypt: bool = True) -> None:
        """Bir profil değeri yazar (varsa günceller).

        Args:
            key: Profil anahtarı.
            value: Saklanacak değer.
            encrypt: ``True`` ise değer diske şifreli yazılır.
        """
        stored = self._cipher.encrypt(value) if encrypt else value
        async with self._session() as session, session.begin():
            entry = await session.get(ProfileEntry, key)
            if entry is None:
                session.add(ProfileEntry(key=key, value=stored, is_encrypted=encrypt))
            else:
                entry.value = stored
                entry.is_encrypted = encrypt
        logger.debug("Profil yazıldı: key=%s, encrypted=%s", key, encrypt)

    async def get(self, key: str) -> str | None:
        """Bir profil değerini okur (şifreliyse çözer).

        Args:
            key: Profil anahtarı.

        Returns:
            Değer; anahtar yoksa ``None``.
        """
        async with self._session() as session:
            entry = await session.get(ProfileEntry, key)
        if entry is None:
            return None
        return self._cipher.decrypt(entry.value) if entry.is_encrypted else entry.value

    async def all(self) -> dict[str, str]:
        """Tüm profil değerlerini (çözülmüş) döndürür.

        Returns:
            Anahtar-değer sözlüğü.
        """
        async with self._session() as session:
            rows = (await session.execute(select(ProfileEntry))).scalars().all()
        result: dict[str, str] = {}
        for entry in rows:
            result[entry.key] = (
                self._cipher.decrypt(entry.value) if entry.is_encrypted else entry.value
            )
        return result

    async def delete(self, key: str) -> None:
        """Bir profil anahtarını siler.

        Args:
            key: Silinecek anahtar.
        """
        async with self._session() as session, session.begin():
            await session.execute(delete(ProfileEntry).where(ProfileEntry.key == key))

    async def close(self) -> None:
        """Veritabanı bağlantı havuzunu kapatır."""
        await self._engine.dispose()
