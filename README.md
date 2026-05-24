# 🤖 J.A.R.V.I.S.

> **Just A Rather Very Intelligent System**
> Yerel-öncelikli, gizliliği koruyan, çok-cihazlı kişisel AI asistan

[![Status](https://img.shields.io/badge/status-alpha-orange)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20iOS%20%7C%20Windows-lightgrey)]()

## ✨ Neler Yapabilir?

- 🎙️ **Sesli komut** — "Hey Jarvis" der demez seni dinler
- 🧠 **Hibrit zeka** — Hızlı görevler MLX, derin düşünme Ollama (Qwen 2.5)
- 📚 **Seni öğrenir** — Tercihlerini, alışkanlıklarını hatırlar
- 🌐 **İnternette araştırır** — Çoklu kaynaktan rapor üretir
- 💻 **Kod yazar** — Geliştirme yardımcısı + shell komutları
- 📅 **Yönetir** — Takvim, mail, dosyalar, hatırlatmalar
- 🏠 **Evi kontrol eder** — HomeKit, Home Assistant entegrasyonu
- 🖥️ **Holografik arayüz** — Gerçek Jarvis hissi veren dinamik UI
- 📱 **Her yerden erişim** — Mac, iPhone, Windows senkronize

## 🏗️ Mimari

```
┌─────────────────────────────────────────────┐
│           HOLO UI · iOS · WINDOWS           │  Layer 01
├─────────────────────────────────────────────┤
│      FAST LANE  ←→  DEEP THINK  ←→  AGENT   │  Layer 02
├─────────────────────────────────────────────┤
│    SHORT-TERM · VECTOR · PROFILE · LEARN    │  Layer 03
├─────────────────────────────────────────────┤
│   WEB · CODE · SHELL · MAIL · CAL · HOME    │  Layer 04
├─────────────────────────────────────────────┤
│        TAILSCALE · API GATEWAY · SYNC       │  Layer 05
└─────────────────────────────────────────────┘
                Mac M4 (16GB)
```

Tam mimari diyagram için: [`docs/architecture.html`](docs/architecture.html)

## 🚀 Hızlı Başlangıç

### Gereksinimler
- macOS (Apple Silicon, M1+)
- Python 3.11+
- Node.js 20+
- 16GB+ RAM
- Tailscale hesabı

### Kurulum

```bash
# Repoyu klonla
git clone https://github.com/fatih/jarvis.git
cd jarvis

# Otomatik kurulum
./scripts/setup.sh

# Ollama'yı başlat
ollama serve &
ollama pull qwen2.5:14b
ollama pull nomic-embed-text

# Servisleri başlat
docker-compose up -d  # Redis + ChromaDB
python -m jarvis.api.main
```

### İlk Konuşma

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Merhaba Jarvis"}'
```

Beklenen çıktı:
```json
{
  "response": "İyi günler efendim. Ne istersiniz?",
  "model": "qwen2.5:14b",
  "latency_ms": 412
}
```

## 📦 Bileşenler

| Modül | Açıklama | Tech |
|-------|----------|------|
| `core/` | Orchestrator, router, agent | Python, LangGraph |
| `models/` | LLM client'ları | Ollama, MLX |
| `memory/` | 3 katmanlı hafıza | Redis, ChromaDB, SQLite |
| `tools/` | Yetenekler | Çeşitli |
| `voice/` | STT/TTS/wake word | Whisper, Piper |
| `api/` | REST + WebSocket | FastAPI |
| `ui/` | Holo UI | React, Three.js |

## 🛠️ Geliştirme

```bash
# Test çalıştır
pytest tests/ -v

# Lint
ruff check .
black .

# Type check
mypy jarvis/

# UI geliştirme
cd ui && npm run dev
```

## 📅 Yol Haritası

- [x] Mimari tasarım
- [~] **Faz 1:** Temel iskelet + Ollama entegrasyonu ← _şu an (kod hazır, model çekilmeyi bekliyor)_
- [ ] **Faz 2:** Hafıza sistemi
- [ ] **Faz 3:** Model router + MLX
- [ ] **Faz 4:** Tools (web, code, shell, vb.)
- [ ] **Faz 5:** Ses katmanı
- [ ] **Faz 6:** Holo UI
- [ ] **Faz 7:** Çoklu cihaz (iOS + Windows)
- [ ] **Faz 8:** Agent + polish

## 🔒 Gizlilik

- ✅ **Tüm veri yerel** — Hiçbir şey buluta gitmiyor
- ✅ **Şifreli depolama** — AES-256 ile DB şifreli
- ✅ **Tailscale VPN** — Cihazlar arası trafik şifreli
- ✅ **Açık kaynak** — Her satırı inceleyebilirsin
- ✅ **Unutma komutu** — "Şunu unut" deyince siler

## 📄 Lisans

MIT © Fatih

## 🙏 Teşekkürler

- [Ollama](https://ollama.com) ekibi
- [MLX](https://github.com/ml-explore/mlx) ekibi
- [Anthropic](https://anthropic.com) — Claude Code ile geliştirildi
