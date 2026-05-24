# api/

FastAPI gateway — REST + WebSocket.

- `main.py` — Uygulama girişi; lifespan, CORS, router kaydı.
- `dependencies.py` — Dependency injection (örn. `OllamaClient` sağlayıcısı).
- `routes/` — Endpoint modülleri (`chat.py`, `health.py`).
- `websocket.py` — (sonraki faz) gerçek zamanlı senkronizasyon.

Çalıştırma: `python -m jarvis.api.main` veya `scripts/run_dev.sh`.
