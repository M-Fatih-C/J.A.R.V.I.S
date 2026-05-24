"""Vektör hafıza — gömülü ChromaDB + dışarıdan enjekte edilen embedder."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any, cast

import chromadb
from chromadb.config import Settings as ChromaSettings
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DEFAULT_COLLECTION = "jarvis_memory"

# Metin listesini embedding vektörlerine çeviren async fonksiyon.
EmbedFn = Callable[[list[str]], Awaitable[list[list[float]]]]


class SearchResult(BaseModel):
    """Bir vektör arama sonucu.

    Attributes:
        id: Kayıt kimliği.
        document: Saklanan metin.
        metadata: İlişkili üst veri.
        distance: Sorguya uzaklık (küçük = daha benzer).
    """

    id: str
    document: str
    metadata: dict[str, Any]
    distance: float


class VectorMemory:
    """ChromaDB üzerinde anlamsal hafıza.

    Embedding üretimi dışarıdan bir :data:`EmbedFn` ile sağlanır (örn.
    ``OllamaClient.embed``), böylece modül LLM client'ından bağımsız test
    edilebilir.

    Attributes:
        collection_name: Kullanılan ChromaDB koleksiyon adı.
    """

    def __init__(
        self,
        embedder: EmbedFn,
        path: str,
        collection_name: str = DEFAULT_COLLECTION,
    ) -> None:
        """VectorMemory'yi başlatır.

        Args:
            embedder: Metinleri vektöre çeviren async fonksiyon.
            path: Kalıcı ChromaDB verisinin tutulacağı dizin.
            collection_name: Koleksiyon adı.
        """
        self._embedder = embedder
        self._client = chromadb.PersistentClient(
            path=path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection_name = collection_name
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def add(
        self,
        document: str,
        metadata: dict[str, Any] | None = None,
        doc_id: str | None = None,
    ) -> str:
        """Bir metni embedding'iyle birlikte hafızaya ekler.

        Args:
            document: Saklanacak metin.
            metadata: İsteğe bağlı üst veri.
            doc_id: Kayıt kimliği; ``None`` ise rastgele UUID üretilir.

        Returns:
            Eklenen kaydın kimliği.
        """
        doc_id = doc_id or str(uuid.uuid4())
        vectors = await self._embedder([document])
        await asyncio.to_thread(
            self._collection.add,
            ids=[doc_id],
            embeddings=cast(Any, vectors),
            documents=[document],
            metadatas=cast(Any, [metadata]) if metadata else None,
        )
        logger.debug("Vektör eklendi: id=%s", doc_id)
        return doc_id

    async def search(self, query: str, n_results: int = 5) -> list[SearchResult]:
        """Sorguya en benzer kayıtları döndürür.

        Args:
            query: Arama metni.
            n_results: Döndürülecek azami sonuç sayısı.

        Returns:
            Benzerliğe göre sıralı :class:`SearchResult` listesi.
        """
        vectors = await self._embedder([query])
        raw = await asyncio.to_thread(
            self._collection.query,
            query_embeddings=cast(Any, vectors),
            n_results=n_results,
        )
        return self._parse_results(cast(dict[str, Any], raw))

    @staticmethod
    def _parse_results(raw: dict[str, Any]) -> list[SearchResult]:
        """ChromaDB ham sorgu çıktısını :class:`SearchResult` listesine çevirir."""
        ids = (raw.get("ids") or [[]])[0]
        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        dists = (raw.get("distances") or [[]])[0]
        results: list[SearchResult] = []
        for i, doc_id in enumerate(ids):
            results.append(
                SearchResult(
                    id=doc_id,
                    document=docs[i] if i < len(docs) else "",
                    metadata=metas[i] if i < len(metas) and metas[i] else {},
                    distance=dists[i] if i < len(dists) else 0.0,
                )
            )
        return results

    async def count(self) -> int:
        """Koleksiyondaki kayıt sayısını döndürür."""
        return await asyncio.to_thread(self._collection.count)

    async def delete(self, doc_id: str) -> None:
        """Verilen kimlikli kaydı siler.

        Args:
            doc_id: Silinecek kaydın kimliği.
        """
        await asyncio.to_thread(self._collection.delete, ids=[doc_id])
        logger.debug("Vektör silindi: id=%s", doc_id)
