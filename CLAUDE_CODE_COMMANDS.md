# 🎯 Claude Code Komut Rehberi — Faz 1

> Bu dosya, Claude Code'a sırasıyla yapıştıracağın komutları içerir.
> Her komut bir adım; bir öncekini tamamladığında sonrakine geç.

---

## 📋 Hazırlık

Önce CLAUDE.md dosyasını proje root'una koy. Claude Code açıldığında otomatik okuyacak.

```bash
cd ~/projects
mkdir jarvis && cd jarvis
# CLAUDE.md ve README.md dosyalarını buraya kopyala
claude  # Claude Code'u başlat
```

---

## KOMUT 1 — Proje İskeleti

```
Lütfen CLAUDE.md'de tanımlanan proje yapısını oluştur.
Tüm klasörleri ve __init__.py dosyalarını ekle.
Her ana modül klasörüne kısa bir README.md koy (modülün ne yaptığını anlat).

Sonra pyproject.toml dosyasını hazırla:
- Python 3.11+
- Proje adı: jarvis
- Versiyon: 0.1.0
- Dependencies: fastapi, uvicorn, ollama, chromadb, redis,
  sqlalchemy, pydantic, python-dotenv, httpx, langchain, langgraph
- Dev dependencies: pytest, pytest-asyncio, ruff, black, mypy

.env.example dosyası hazırla, .gitignore yaz, MIT lisans ekle.
```

---

## KOMUT 2 — Ollama Client

```
models/ollama_client.py dosyasını oluştur.

Gereksinimler:
- OllamaClient sınıfı (async)
- Constructor: base_url (default http://localhost:11434), default_model (qwen2.5:14b)
- chat(messages, model=None, stream=False) → ChatResponse
- chat_stream(messages, model=None) → AsyncIterator
- list_models() → List[str]
- health_check() → bool

Pydantic modelleri:
- ChatMessage(role: Literal["system","user","assistant"], content: str)
- ChatResponse(content, model, latency_ms, tokens)

models/base.py'de LLMClient abstract base class olsun;
OllamaClient ondan inherit etsin.

Logging ekle (logging modülü).
Type hints zorunlu.
Docstring (Google style) zorunlu.

tests/test_ollama_client.py içinde mock'lu birim testler yaz.
```

---

## KOMUT 3 — Config & Settings

```
config/settings.py dosyasını oluştur.

Pydantic Settings kullan (pydantic-settings paketi).
.env dosyasından okusun.

Tanımlanacak ayarlar:
- App: APP_NAME, ENV (dev/prod), DEBUG, LOG_LEVEL
- Server: HOST, PORT
- Ollama: OLLAMA_URL, OLLAMA_DEFAULT_MODEL, OLLAMA_EMBED_MODEL
- Redis: REDIS_URL
- ChromaDB: CHROMA_PATH
- SQLite: SQLITE_PATH, SQLITE_ENCRYPTION_KEY
- Security: JWT_SECRET, JWT_ALGORITHM

settings = Settings() singleton olarak export et.
.env.example dosyasını da güncelle.
```

---

## KOMUT 4 — FastAPI İskelet

```
api/main.py dosyasını oluştur.

FastAPI app:
- Title: "Jarvis API"
- CORS middleware (tüm origin'ler dev'de)
- Lifespan event (startup'ta Ollama health check)
- /health endpoint → {"status": "ok", "ollama": bool}
- /chat endpoint (POST) → mesajı Ollama'ya gönder, yanıt dön
  - Request: ChatRequest(message: str, model: Optional[str])
  - Response: ChatResponse

api/routes/ klasörü oluştur, /chat'i route'a taşı.
api/dependencies.py'de OllamaClient için dependency injection ekle.

scripts/run_dev.sh script'i:
- Ollama health check
- uvicorn ile API'yi başlat (reload mode)
```

---

## KOMUT 5 — End-to-End Test

```
İlk uçtan uca test:

1. docker-compose.yml hazırla:
   - Redis (port 6379)
   - ChromaDB (port 8001)
   - volumes: data/ klasörüne mount

2. scripts/setup.sh:
   - Python venv oluştur
   - Dependencies kur
   - .env dosyası oluştur (.env.example'dan)
   - Ollama kurulu mu kontrol et
   - qwen2.5:14b modeli var mı kontrol et, yoksa indir

3. tests/test_e2e.py:
   - API başlatılır
   - /health çağırılır
   - /chat ile "Merhaba" gönderilir
   - Yanıt 5 saniye içinde gelir
   - Yanıtta "merhaba" veya benzer kelime var

Tüm script'leri çalıştırılabilir yap (chmod +x).
README'yi güncelle: "Hızlı Başlangıç" bölümünü test et.
```

---

## KOMUT 6 — Faz 1 Tamamlama

```
Faz 1 tamamlandı. Lütfen:

1. Tüm testleri çalıştır (pytest -v)
2. Lint kontrolü yap (ruff check . && black --check .)
3. Type check (mypy jarvis/)
4. CLAUDE.md'deki Faz 1 checkbox'larını işaretle
5. CHANGELOG.md oluştur, Faz 1 değişikliklerini listele
6. İlk git commit'i hazırla (conventional commits formatında)
7. Faz 2 planını özetle (memory sistemi)

Hazır olduğunda bana özet ver, Faz 2'ye geçelim.
```

---

## 💡 Genel İpuçları

### Claude Code ile En Verimli Çalışma

1. **Komutu yapıştırdıktan sonra bekle.** Plan modunda önce ne yapacağını anlatacak, onayla.
2. **Küçük adımlar.** Tek seferde çok şey isteme; modül bazında ilerle.
3. **Test çalıştırmasını iste.** "Sonra testi çalıştır" deyince commit öncesi doğrular.
4. **Hata olursa.** "Hatayı debug et, kök nedeni bul" de.
5. **MCP'leri kullan.** "GitHub MCP ile yeni branch aç" gibi komutlar verebilirsin.

### NotebookLM ile Köprü

Her büyük değişiklikten sonra:
1. Değişen dosyaları zip'le
2. NotebookLM'e yükle ("project-state-v0.X.zip")
3. Yeni özellik düşünürken NotebookLM'e sor: "Bu mimariye uyar mı?"
4. Cevabı Claude Code'a yapıştır

### Yaygın Hatalar

❌ Tek seferde tüm projeyi yazdırma → Hata bulması zorlaşır
✅ Modül modül ilerle, her birini test et

❌ "Düzelt" demek → Çok geniş
✅ "X dosyasındaki Y hatası: şu satırda Z bekliyor" → Spesifik

❌ Plan onaylamadan kod yazdırmak
✅ Önce plan al, gerekirse düzelt, sonra kodla

---

## 🎓 Faz 2'ye Geçiş Kriterleri

Faz 1'i bitirmeden Faz 2'ye geçme. Bitirme kriterleri:

- [ ] `/health` endpoint dönüyor
- [ ] `/chat` ile Ollama'ya mesaj gidip yanıt dönüyor
- [ ] Latency < 3 saniye (Qwen 2.5 14B için normal)
- [ ] Tüm testler geçiyor
- [ ] README'deki kurulum talimatları sıfırdan çalışıyor
- [ ] Docker Compose ile Redis + ChromaDB ayağa kalkıyor
- [ ] İlk commit GitHub'da

Bu liste tamamlanınca Faz 2 (Hafıza Sistemi) komutlarını hazırlarım.
