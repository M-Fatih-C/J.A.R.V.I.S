"""Prometheus metrikleri — katmandan bağımsız (core ve api kullanır)."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

CONTENT_TYPE = CONTENT_TYPE_LATEST

REQUESTS = Counter(
    "jarvis_requests_total",
    "Toplam HTTP isteği",
    ["method", "path", "status"],
)
LATENCY = Histogram(
    "jarvis_request_duration_seconds",
    "HTTP istek süresi (saniye)",
    ["method", "path"],
)
CHAT_LANE = Counter(
    "jarvis_chat_total",
    "İşlem hattına göre sohbet sayısı",
    ["lane"],
)
ERRORS = Counter(
    "jarvis_errors_total",
    "Türe göre hata sayısı",
    ["kind"],
)


def render() -> bytes:
    """Mevcut metrikleri Prometheus metin formatında döndürür."""
    return generate_latest()
