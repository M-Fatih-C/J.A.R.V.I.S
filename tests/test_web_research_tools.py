"""web_search ve research (fetch_url) araçları için testler — ağ mock'lu."""

from __future__ import annotations

from typing import Any

from jarvis.tools.research import FetchUrlTool
from jarvis.tools.web_search import WebSearchTool

# ── web_search ──


async def test_web_search_formats_results() -> None:
    def fake_search(query: str, max_results: int) -> list[dict[str, Any]]:
        return [
            {"title": "Sonuç 1", "href": "http://a", "body": "özet 1"},
            {"title": "Sonuç 2", "href": "http://b", "body": "özet 2"},
        ]

    tool = WebSearchTool(search_fn=fake_search)
    out = await tool.run(query="jarvis")
    assert "Sonuç 1" in out
    assert "http://a" in out
    assert "özet 2" in out


async def test_web_search_no_results() -> None:
    tool = WebSearchTool(search_fn=lambda q, n: [])
    assert "bulunamadı" in await tool.run(query="xyz")


async def test_web_search_handles_error() -> None:
    def boom(query: str, max_results: int) -> list[dict[str, Any]]:
        raise RuntimeError("ağ yok")

    tool = WebSearchTool(search_fn=boom)
    out = await tool.run(query="x")
    assert "başarısız" in out


async def test_web_search_respects_max_results() -> None:
    captured: dict[str, int] = {}

    def fake_search(query: str, max_results: int) -> list[dict[str, Any]]:
        captured["n"] = max_results
        return []

    await WebSearchTool(search_fn=fake_search, max_results=3).run(query="x")
    assert captured["n"] == 3


# ── research / fetch_url ──


async def test_fetch_url_strips_html() -> None:
    async def fake_fetch(url: str) -> str:
        return "<html><body><h1>Başlık</h1><p>Gövde metni</p></body></html>"

    tool = FetchUrlTool(fetch_fn=fake_fetch)
    out = await tool.run(url="http://x")
    assert "Başlık" in out
    assert "Gövde metni" in out
    assert "<" not in out


async def test_fetch_url_removes_script() -> None:
    async def fake_fetch(url: str) -> str:
        return "<p>iyi</p><script>alert('kötü')</script>"

    out = await FetchUrlTool(fetch_fn=fake_fetch).run(url="http://x")
    assert "iyi" in out
    assert "alert" not in out


async def test_fetch_url_truncates() -> None:
    async def fake_fetch(url: str) -> str:
        return "<p>" + ("a" * 100) + "</p>"

    out = await FetchUrlTool(fetch_fn=fake_fetch, max_chars=20).run(url="http://x")
    assert "kırpıldı" in out


async def test_fetch_url_handles_error() -> None:
    async def boom(url: str) -> str:
        raise RuntimeError("404")

    out = await FetchUrlTool(fetch_fn=boom).run(url="http://x")
    assert "getirilemedi" in out
