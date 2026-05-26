# Changelog

Bu projedeki tüm önemli değişiklikler bu dosyada belgelenir.
Format [Keep a Changelog](https://keepachangelog.com/) temellidir;
sürümleme [Semantic Versioning](https://semver.org/) izler.

## [Unreleased]

### Eklendi / Değişti
- **Deep Think canlı:** `qwen2.5:14b` çekildi; `/chat` deep lane (araştırma/
  analiz/açıklama mesajları) Ollama/Qwen ile **canlı doğrulandı** (Türkçe,
  "efendim" hitabı). Artık her iki hat da uçtan uca çalışıyor.
- **E2E testleri yenilendi:** `test_chat_fast_lane` + `test_chat_deep_lane`
  (yeni mimariye göre lane doğrular). Katı gecikme sınırı kaldırıldı (yerel
  LLM'ler donanıma göre değişir). Gerçek model testleri `JARVIS_E2E=1` ile
  açılır; deep lane modeli yoksa skip.

## [0.4.0] — 2026-05-26

**Orchestrator entegrasyonu** — Faz 1-3 tek uçtan uca akışta birleşti.

### Eklendi
- **Orchestrator:** `core/orchestrator.py` — Router ile lane seçer, kısa süreli
  hafızadan bağlam + sistem prompt ekler, yanıtı üretir ve konuşmayı hafızaya
  geri yazar. Redis erişilemezse durumsuz (stateless) devam eder. `ChatResult`
  modeli lane + gerekçe döndürür.
- **DI:** `get_mlx_client`, `get_router`, `get_short_term_memory`,
  `get_orchestrator` sağlayıcıları.

### Değişti
- `/chat` artık Orchestrator üzerinden çalışıyor; istek `session_id` alır,
  yanıt `lane`/`reason` içerir. Fast Lane (MLX) uçtan uca **canlı doğrulandı**
  (~0.5s, temiz Türkçe yanıt).
- `MLXClient`: modelin `eos_token_id`'si durdurma kümesine eklendi (üretim
  artık tur sonunda duruyor) ve çıktıya sızan özel token'lar kırpılıyor.
  Gecikme örnekte 13s → ~0.3s'ye düştü.

### Test
- Yeni: `test_orchestrator` (sahte client + fakeredis). Toplam **73 test**, 2 skip.

## [0.3.0] — 2026-05-26

**Faz 3: Model Router + MLX** — Fast Lane (MLX) ile Deep Think (Ollama) ayrımı.

### Eklendi
- **MLX client:** `models/mlx_client.py` — Apple MLX üzerinde Phi-3.5 Mini
  (4bit) çalıştıran async `MLXClient`. **Lazy loading** (ilk istekte yüklenir),
  `unload()` ile RAM boşaltma, `chat` + thread-queue tabanlı `chat_stream`.
- **Router:** `core/router.py` — kural tabanlı `Router`; mesaj uzunluğu,
  derin-düşünme anahtar kelimeleri ve cümle/soru karmaşıklığına göre
  `Lane.FAST` ↔ `Lane.DEEP` kararı verir (`route`, `pick_client`).
- **Benchmark:** `scripts/benchmark.py` — MLX vs Ollama gecikme/throughput
  karşılaştırması (Ollama modeli yoksa atlar).

### Bağımlılıklar
- Yeni opsiyonel `[mlx]` extra: `mlx-lm` (Apple Silicon). Kurulum:
  `uv sync --extra mlx`.

### Test
- Yeni: `test_mlx_client` (mlx_lm mock'lu), `test_router` (parametrik),
  `test_mlx_smoke` (gerçek model, `JARVIS_MLX_SMOKE=1` ile). Toplam
  **67 test geçiyor**, 2 skip. Gerçek çıkarım elle doğrulandı (~37 tok/s).

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
