# CLAUDE.md — Jarvis Project Context

> Bu dosya Claude Code tarafından her oturum başında otomatik okunur.
> Proje mimarisi, kuralları ve hedefleri burada tanımlıdır.

---

## 🎯 Proje Tanımı

**Jarvis**, Fatih için geliştirilen yerel-öncelikli (local-first), gizliliği koruyan, çok-cihazlı kişisel AI asistandır. Mac M4 (16GB) sunucu olarak çalışır; iPhone ve Windows istemcileri Tailscale VPN üzerinden bağlanır.

### Ana Özellikler
- 🎙️ Sesli komut (wake word: "Hey Jarvis")
- 🧠 Hibrit LLM (MLX hızlı + Ollama derin düşünme)
- 📚 3 katmanlı hafıza (kısa süreli + vector + yapılandırılmış)
- 🌐 İnternet araştırması ve raporlama
- 💻 Kod yazma ve shell komutları çalıştırma
- 📅 Takvim, mail, dosya, ev otomasyonu entegrasyonu
- 🖥️ Dinamik "Holo UI" arayüz (gerçek Jarvis hissi)
- 🔄 Pasif öğrenme (kullanıcı tercihlerini öğrenir)

---

## 🏗️ Mimari Katmanlar

### Layer 01 — Interface
- **Voice I/O:** Whisper.cpp (STT) + Piper (TTS) + openWakeWord
- **Holo UI:** React + WebSocket + Three.js
- **iOS Client:** SwiftUI + Shortcuts
- **Windows Client:** Python + PyQt6

### Layer 02 — Cognitive Core
- **Fast Lane:** MLX + Phi-3.5 Mini (3.8B) → niyet tespiti, basit komutlar
- **Deep Think:** Ollama + Qwen 2.5 14B → tool calling, agent görevleri
- **Router:** Python custom logic
- **Agent Engine:** LangGraph (ReAct pattern)
- **Orchestrator:** FastAPI + AsyncIO

### Layer 03 — Memory & Learning
- **Short-term:** Redis (in-memory)
- **Vector Memory:** ChromaDB + nomic-embed-text
- **User Profile:** SQLite (encrypted)
- **Learning Engine:** Background worker (otomatik özetleme)
- **Personality:** Dynamic system prompts

### Layer 04 — Tools & Capabilities
- Web Search (SearXNG/Brave), Research (multi-step), Reporting (Pandoc),
  Code Writer (Qwen Coder + sandbox), Shell Exec (subprocess + Docker),
  Calendar (Google/CalDAV), Email (IMAP/SMTP), File System, Home Assistant

### Layer 05 — Network & Infrastructure
- Tailscale VPN, FastAPI Gateway, JWT + AES-256, WebSocket sync,
  Prometheus + Grafana monitoring

---

## 📁 Proje Yapısı

```
jarvis/
├── core/                    # Orchestrator, router, agent engine
│   ├── orchestrator.py
│   ├── router.py
│   └── agent.py
├── models/                  # LLM client'ları
│   ├── ollama_client.py
│   ├── mlx_client.py
│   └── base.py
├── memory/                  # 3 katmanlı hafıza
│   ├── short_term.py        # Redis
│   ├── vector_store.py      # ChromaDB
│   ├── profile.py           # SQLite
│   └── learning.py          # Pasif öğrenme
├── tools/                   # Yetenekler (tool calling)
│   ├── web_search.py
│   ├── research.py
│   ├── code_writer.py
│   ├── shell_exec.py
│   ├── calendar_tool.py
│   ├── email_tool.py
│   └── file_system.py
├── voice/                   # Ses katmanı
│   ├── stt.py               # Whisper
│   ├── tts.py               # Piper
│   └── wake_word.py
├── api/                     # FastAPI gateway
│   ├── main.py
│   ├── routes/
│   └── websocket.py
├── ui/                      # Holo UI (React)
│   ├── src/
│   ├── public/
│   └── package.json
├── clients/                 # Diğer cihazlar
│   ├── ios/                 # SwiftUI projesi
│   └── windows/             # PyQt6 app
├── config/
│   ├── settings.py
│   └── prompts/
├── tests/
├── scripts/                 # Setup, deploy script'leri
├── pyproject.toml
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## 📐 Geliştirme Kuralları

### Kod Standartları
- **Python:** 3.11+, type hints zorunlu, `ruff` + `black` ile formatla
- **Async-first:** Tüm I/O işlemleri `async/await` kullanmalı
- **Dependency injection:** Sınıflar bağımlılıkları constructor'dan alır
- **Error handling:** Try/except blokları log'lamalı, sessizce yutmamalı
- **Testler:** Her modül için pytest, en az %60 coverage hedefi

### İsimlendirme
- Sınıflar: `PascalCase` (örn. `OllamaClient`)
- Fonksiyonlar/değişkenler: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Async fonksiyonlar: `async def` ön ek "a_" değil, doğrudan isim

### Dokümantasyon
- Her public fonksiyon docstring (Google style)
- Karmaşık logic için inline yorum (Türkçe veya İngilizce, tutarlı)
- README'lerde Türkçe ana dil

### Güvenlik
- API anahtarları **asla** kod içinde değil, `.env` dosyasında
- Kullanıcı verisi SQLite'da AES-256 ile şifreli
- Shell exec sandboxlanmış (Docker container içinde)
- Tüm cihazlar Tailscale ile auth + JWT

---

## 🔌 MCP Sunucuları (Claude Code için)

Bu projede şu MCP sunucuları aktif olmalı:

| MCP | Scope | Kullanım |
|-----|-------|----------|
| GitHub | user | Repo yönetimi, commits, PR |
| Brave Search | user | Web araştırması test |
| Memory | project | Oturumlar arası bağlam |
| SQLite | project | User profile DB sorguları |
| Playwright | project | UI testleri |
| Sequential Thinking | user | Karmaşık planlama |

Kurulum komutları `scripts/setup_mcp.sh` dosyasında.

---

## 🎨 Konuşma Tarzı (Jarvis Personality)

Jarvis kullanıcıyla konuşurken:
- **Hitap:** "efendim" (resmi ama samimi)
- **Ton:** Sakin, kendinden emin, hafif İngiliz uşağı havası
- **Dil:** Türkçe (varsayılan), İngilizce gerekirse
- **Uzunluk:** Kısa ve öz, gereksiz açıklama yok
- **Proaktiflik:** Tahminde bulunur ama sormadan eylem yapmaz
- **Mizah:** Hafif, kuru, asla saygısız değil

### Örnek
❌ "Tamam, hemen yapıyorum!"
✅ "Elbette efendim. Mail taslağı hazır."

❌ "Bilemiyorum, üzgünüm."
✅ "Bu konuda yetersiz veriyle yanıt vermek istemem efendim. Araştırmamı ister misiniz?"

---

## 🚦 Geliştirme Fazları

### Faz 1 — Temel İskelet (1-2 hafta) ⬅ ŞU AN BURADAYIZ
- [x] Proje klasör yapısını oluştur
- [x] Ollama kurulumu + Qwen 2.5 14B çek (model yüklü, deep lane canlı)
- [x] `models/ollama_client.py` — temel sohbet (+ base.py, mock'lu testler)
- [x] `api/main.py` — FastAPI iskelet (/health, /chat, lifespan, CORS, DI)
- [x] İlk uçtan-uca text chat çalışıyor (Fast Lane/MLX + Deep Think/Qwen canlı doğrulandı)

### Faz 2 — Hafıza Sistemi (2 hafta)
- [x] `memory/short_term.py` (Redis)
- [x] `memory/vector_store.py` (ChromaDB + embedding)
- [x] `memory/profile.py` (SQLite şema)
- [x] `memory/learning.py` (otomatik özet)
- [x] Hafıza CRUD testleri

### Faz 3 — Model Router + MLX (1-2 hafta)
- [x] `models/mlx_client.py` (Phi-3.5 Mini 4bit, lazy load/unload)
- [x] `core/router.py` (kural tabanlı niyet tespiti)
- [x] Lazy loading mekanizması
- [x] Performance benchmark (`scripts/benchmark.py`)

### Faz 4 — Tools (2-3 hafta)
- [x] Tool calling altyapısı (Tool/ToolRegistry + LangGraph ReAct agent)
- [x] Web search + research (DuckDuckGo + fetch_url)
- [x] Code writer + sandbox (run_python — subprocess + guardrail)
- [x] Shell exec (güvenli — subprocess + guardrail)
- [x] Calendar, email, file system (file_system tam; calendar/email iskelet)

### Faz 5 — Ses Katmanı (1-2 hafta)
- [ ] Whisper.cpp entegrasyonu
- [ ] Piper TTS
- [ ] Wake word ("Hey Jarvis")
- [ ] Real-time streaming

### Faz 6 — Holo UI (2-3 hafta)
- [ ] React + TypeScript setup
- [ ] WebSocket bağlantısı
- [ ] Dinamik görselleştirme (sesli dalga, durum)
- [ ] Üç boyutlu efektler (Three.js)

### Faz 7 — Çoklu Cihaz (2 hafta)
- [ ] Tailscale kurulumu
- [ ] iOS app (SwiftUI)
- [ ] Windows app (PyQt6)
- [ ] Senkronizasyon

### Faz 8 — Agent + Polishing (2 hafta)
- [ ] LangGraph agent flow'ları
- [ ] Hata yakalama, retry
- [ ] Monitoring (Prometheus)
- [ ] Production-ready

---

## 🤖 Claude Code'a Talimatlar

Bu projede çalışırken:

1. **Önce planla, sonra kodla.** Karmaşık görevlerde önce kısa bir plan yaz, onay al.
2. **Mevcut kod stilini koru.** Yeni bir patternı tek başına devreye sokma.
3. **Test yaz.** Her yeni modül için en az bir test ekle.
4. **README güncelle.** İlgili modülün README'sini değiştir.
5. **Commit message'lar:** Conventional Commits formatı (`feat:`, `fix:`, `docs:`, vb.)
6. **Soruyu sor.** Belirsizlik varsa varsayım yapma, sor.
7. **Türkçe dokümantasyon, İngilizce kod.** Kod isimleri İngilizce, README ve yorumlar Türkçe.

### Faz Geçişleri
Bir faz bittiğinde:
- README'deki checkbox'ları işaretle
- O fazın test'lerini çalıştır
- Bir sonraki faz için onay iste

---

## 📚 Referans Kaynaklar

- Ollama: https://ollama.com/library/qwen2.5
- MLX: https://github.com/ml-explore/mlx
- ChromaDB: https://docs.trychroma.com
- LangGraph: https://langchain-ai.github.io/langgraph/
- Whisper.cpp: https://github.com/ggerganov/whisper.cpp
- Piper TTS: https://github.com/rhasspy/piper
- Tailscale: https://tailscale.com/kb/

---

**Son güncelleme:** 2026-05-24
**Versiyon:** 1.0.0-alpha
**Sahibi:** Fatih
