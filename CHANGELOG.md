# Changelog

Bu projedeki tüm önemli değişiklikler bu dosyada belgelenir.
Format [Keep a Changelog](https://keepachangelog.com/) temellidir;
sürümleme [Semantic Versioning](https://semver.org/) izler.

## [0.2.0] — 2026-05-25

**Faz 2: Hafıza Sistemi** — 3 katmanlı hafıza + pasif öğrenme.

### Eklendi
- **Kısa süreli hafıza:** `memory/short_term.py` — Redis (async) tabanlı,
  oturum bazlı konuşma penceresi; `max_messages` kırpma + TTL yenileme.
- **Vektör hafıza:** `memory/vector_store.py` — gömülü ChromaDB
  (PersistentClient, kosinüs); embedding dışarıdan enjekte edilir
  (`EmbedFn`), `add`/`search`/`count`/`delete`.
- **Kullanıcı profili:** `memory/profile.py` — async SQLAlchemy (aiosqlite)
  anahtar-değer deposu; hassas alanlar `Cipher` ile **AES-256-GCM** şifreli.
- **Öğrenme motoru:** `memory/learning.py` — oturumları LLM ile özetleyip
  vektör hafızaya pekiştiren `LearningEngine` + periyodik worker.
- **Embedding:** `OllamaClient.embed()` (+ `embed_model`) — `/api/embed`,
  `nomic-embed-text`.

### Değişti
- `api/dependencies.py` — Ollama client'ı `embed_model` ile yapılandırılıyor.

### Bağımlılıklar
- Eklendi: `cryptography`, `aiosqlite`, `greenlet` (main); `fakeredis` (dev).

### Test
- Yeni: `test_short_term` (fakeredis), `test_vector_store` (sahte embedder),
  `test_profile`, `test_learning`. Toplam **42 test geçiyor**, 1 skip (e2e).

## [0.1.0] — 2026-05-25

İlk iskelet sürümü — **Faz 1: Temel İskelet**.

### Eklendi
- **Proje yapısı:** `jarvis/` paketi altında `core`, `models`, `memory`,
  `tools`, `voice`, `api`, `config` modülleri; her modül için README.
- **Paketleme:** `pyproject.toml` (uv, Python 3.11+), ruff + black + mypy +
  pytest yapılandırması, `.env.example`, `.gitignore`, MIT `LICENSE`.
- **LLM katmanı:** `models/base.py` (`LLMClient` ABC + `ChatMessage` /
  `ChatResponse` Pydantic modelleri) ve `models/ollama_client.py`
  (async `OllamaClient`: `chat`, `chat_stream`, `list_models`,
  `health_check`).
- **Config:** `config/settings.py` — `pydantic-settings` tabanlı, `.env`'den
  okuyan `settings` singleton'ı.
- **API:** `api/main.py` (lifespan'da Ollama health check, CORS),
  `/health` ve `/chat` endpoint'leri, `api/dependencies.py` ile DI,
  Jarvis kişilik sistem prompt'u.
- **Altyapı:** `docker-compose.yml` (Redis + ChromaDB), `scripts/setup.sh`,
  `scripts/run_dev.sh`.
- **Testler:** `tests/test_ollama_client.py` (mock'lu birim testler) ve
  `tests/test_e2e.py` (model yoksa otomatik atlanır). 9 test geçiyor.

### Notlar
- Ollama sunucusu çalışıyor ancak `qwen2.5:14b` modeli henüz çekilmedi;
  uçtan uca `/chat` testi model çekilene kadar atlanıyor (skip).
