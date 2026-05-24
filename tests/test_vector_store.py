"""VectorMemory için testler — sahte embedder ile (Ollama/model gerekmez)."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.memory.vector_store import SearchResult, VectorMemory

# Basit, deterministik embedding: kelimeyi 3 boyutlu bir baz vektöre eşler.
_VECTORS: dict[str, list[float]] = {
    "kedi": [1.0, 0.0, 0.0],
    "köpek": [0.0, 1.0, 0.0],
    "araba": [0.0, 0.0, 1.0],
}


async def fake_embedder(texts: list[str]) -> list[list[float]]:
    """Metni içindeki anahtar kelimeye göre sabit bir vektöre eşler."""
    out: list[list[float]] = []
    for t in texts:
        vec = [0.0, 0.0, 0.0]
        for word, v in _VECTORS.items():
            if word in t.lower():
                vec = v
                break
        out.append(vec)
    return out


@pytest.fixture
def store(tmp_path: Path) -> VectorMemory:
    """Geçici dizinde gömülü bir VectorMemory."""
    return VectorMemory(
        embedder=fake_embedder,
        path=str(tmp_path / "chroma"),
        collection_name="test_mem",
    )


async def test_add_returns_id_and_increments_count(store: VectorMemory) -> None:
    assert await store.count() == 0
    doc_id = await store.add("kedi sevimli bir hayvandır")
    assert isinstance(doc_id, str)
    assert await store.count() == 1


async def test_add_with_explicit_id(store: VectorMemory) -> None:
    returned = await store.add("köpek havlar", doc_id="d1")
    assert returned == "d1"


async def test_search_returns_nearest(store: VectorMemory) -> None:
    await store.add("kedi sevimli", doc_id="kedi-doc")
    await store.add("araba hızlı", doc_id="araba-doc")

    results = await store.search("kedi", n_results=1)
    assert len(results) == 1
    assert isinstance(results[0], SearchResult)
    assert results[0].id == "kedi-doc"


async def test_search_preserves_metadata(store: VectorMemory) -> None:
    await store.add("köpek sadık", metadata={"tür": "hayvan"}, doc_id="k1")
    results = await store.search("köpek", n_results=1)
    assert results[0].metadata.get("tür") == "hayvan"


async def test_delete(store: VectorMemory) -> None:
    await store.add("kedi", doc_id="x1")
    assert await store.count() == 1
    await store.delete("x1")
    assert await store.count() == 0


async def test_search_empty_store(store: VectorMemory) -> None:
    results = await store.search("kedi")
    assert results == []
