# 📚 Jarvis Project — Master Document (NotebookLM)

> Bu dosyayı NotebookLM'e yükle. Projenin "beyni" olarak kullanacak.
> Tüm soruları bu dosyadan cevaplayabilecek.

---

# BÖLÜM 1: PROJE VİZYONU

## 1.1 Ne İnşa Ediyoruz?

**Jarvis**, Iron Man filmlerindeki AI asistandan esinlenen, Fatih için özelleştirilmiş bir yerel-öncelikli kişisel asistandır. Ana farkları:

- **Yerel çalışır** — Hiçbir veri buluta gitmez
- **Çoklu cihaz** — Mac (sunucu), iPhone, Windows entegre
- **Açık kaynak modeller** — Llama, Qwen, Mistral
- **Öğrenir** — Kullanıcıyı tanır, tercihlerini hatırlar
- **Eyleme geçer** — Sadece konuşmaz, iş yapar (kod yazar, mail atar, vb.)

## 1.2 Donanım

- **Sunucu:** Mac M4, 16GB RAM (her zaman açık)
- **İstemciler:** iPhone, Windows PC
- **Ağ:** Tailscale VPN ile birbirine bağlı

## 1.3 Tasarım Felsefesi

1. **Privacy-first:** Local data, encrypted storage, no telemetry
2. **Modular:** Her bileşen değiştirilebilir (Ollama → MLX, ChromaDB → Qdrant)
3. **Async-first:** Her şey paralel çalışabilmeli
4. **Voice-native:** Ses doğal arayüz, metin ikinci sırada
5. **Personality matters:** Sadece akıllı değil, karakterli

---

# BÖLÜM 2: MİMARİ

## 2.1 5 Katmanlı Yapı

### Layer 01 — Interface (Kullanıcıyla Temas)

| Bileşen | Teknoloji | Rol |
|---------|-----------|-----|
| Voice Input | Whisper.cpp + openWakeWord | Sesi metne çevirir |
| Voice Output | Piper TTS | Metni sese çevirir |
| Holo UI | React + Three.js + WebSocket | Görsel dinamik arayüz |
| iOS Client | SwiftUI | iPhone uygulaması |
| Windows Client | PyQt6 | Windows tray app |

### Layer 02 — Cognitive Core (Beyin)

| Bileşen | Teknoloji | Rol |
|---------|-----------|-----|
| Fast Lane | MLX + Phi-3.5 Mini (3.8B) | Hızlı yanıt, niyet tespiti, <500ms |
| Deep Think | Ollama + Qwen 2.5 14B (Q4) | Karmaşık görevler, tool calling |
| Router | Python custom | Görevi doğru motora yönlendirir |
| Agent Engine | LangGraph (ReAct) | Çok adımlı planlama ve yürütme |
| Orchestrator | FastAPI + AsyncIO | Tüm bileşenleri koordine eder |

### Layer 03 — Memory & Learning (Hafıza)

**3 katmanlı hafıza yapısı:**

| Katman | Teknoloji | Saklanan |
|--------|-----------|----------|
| Short-term | Redis | Aktif konuşmanın son N mesajı |
| Vector | ChromaDB + nomic-embed | Tüm anılar, semantic arama için |
| Profile | SQLite (encrypted) | Yapılandırılmış kişisel bilgi |

**Öğrenme modları:**
- **Pasif:** Her konuşma sonrası özet çıkarılır, vector DB'ye yazılır
- **Aktif:** "Bunu hatırla" → Profile'a işlenir
- **Geri bildirim:** "Hayır, bu yanlıştı" → Düzeltir

### Layer 04 — Tools (Yetenekler)

- **Web Search:** SearXNG veya Brave Search API
- **Research:** Multi-step agent (ara → analiz → sentezle)
- **Reporting:** Pandoc ile PDF/Markdown rapor
- **Code Writer:** Qwen Coder + Docker sandbox
- **Shell Exec:** subprocess + güvenli sandbox
- **Calendar:** Google Calendar API / CalDAV
- **Email:** Gmail API / IMAP-SMTP
- **File System:** OS-level dosya erişimi
- **Home Control:** Home Assistant / HomeKit

### Layer 05 — Network & Infrastructure

- **Tailscale VPN:** Cihazlar arası güvenli ağ
- **API Gateway:** FastAPI + Nginx
- **Auth:** JWT tokens
- **Encryption:** AES-256 (DB), TLS (network)
- **Monitoring:** Prometheus + Grafana

## 2.2 Veri Akışı (Örnek)

**Senaryo:** "Jarvis, bu hafta AI haberlerini araştır ve rapor hazırla"

```
1. VOICE INPUT — Whisper sesi metne çevirir
2. ROUTER — MLX hızlıca: "Karmaşık görev, agent gerekir"
3. MEMORY — Profil'den "Fatih'in AI ilgi alanları" çekilir
4. AGENT PLAN — Qwen 14B planı parçalar: ara → analiz → özetle
5. WEB SEARCH — Çoklu sorgu, kaynak toplama
6. REPORTING — Markdown rapor → PDF
7. HOLO UI — Gerçek zamanlı ilerleme gösterilir
8. VOICE OUTPUT — "Rapor hazır efendim"
9. LEARNING — "Pazar sabahları rapor istiyor" → Vector DB
```

## 2.3 RAM Bütçesi (16GB)

| Bileşen | RAM |
|---------|-----|
| macOS | ~4 GB |
| MLX + Phi-3.5 (lazy load) | ~2.5 GB |
| Ollama + Qwen 14B Q4 | ~8.5 GB |
| Whisper + TTS + Backend | ~1 GB |

Sınırda. Lazy loading kritik — MLX modeli kullanılmadığında boşaltılır.

---

# BÖLÜM 3: TEKNİK KARARLAR (NEDEN?)

## 3.1 Neden Yerel?

- **Gizlilik:** Mail, takvim, kişisel anılar bulutta olmasın
- **Latency:** Lokal yanıt > 100ms, API > 500ms
- **Cost:** API ücreti yok, bir kere kur, sınırsız kullan
- **Offline:** İnternet olmadığında bile temel görevler

## 3.2 Neden Ollama + MLX İkisi Birden?

- **Ollama:** Kolay setup, geniş model desteği, OpenAI uyumlu API
- **MLX:** Apple Silicon'da %30-50 daha hızlı, daha az RAM
- **Hibrit:** Basit görevler MLX (hızlı), karmaşık Ollama (akıllı)
- **Trade-off:** Setup karmaşıklığı artar, ama performans çok daha iyi

## 3.3 Neden Qwen 2.5 14B?

- **Tool calling:** Sınıfının en iyilerinden
- **Türkçe:** Llama'dan daha iyi Türkçe anlıyor
- **16GB'a sığar:** Q4 quantization ile ~8GB
- **Hız:** M4'te ~30 token/sn

## 3.4 Neden ChromaDB?

- **Local-first:** Sunucu gerektirmez, embedded
- **Python native:** Kurulum kolay
- **Metadata filtering:** "Sadece son hafta" gibi sorgular
- **Persistence:** Diske yazıyor, restart sonrası kayıp yok

## 3.5 Neden FastAPI?

- **Async native:** Performance kritik bir asistanda gerekli
- **WebSocket desteği:** Real-time UI için
- **Pydantic:** Type safety, otomatik dokümantasyon
- **Ekosistem:** En geniş Python topluluğu

## 3.6 Neden Tailscale?

- **WireGuard:** Hızlı, modern, güvenli
- **MagicDNS:** "mac.local" gibi isimlerle erişim
- **NAT traversal:** Router ayarı gerekmez
- **Ücretsiz:** 100 cihaza kadar

---

# BÖLÜM 4: GELİŞTİRME SÜRECİ

## 4.1 Araçlar

- **IDE:** Cursor veya VS Code
- **AI Assistant:** Claude Code (CLI)
- **Project Memory:** NotebookLM (bu döküman)
- **Version Control:** Git + GitHub
- **MCP Servers:** GitHub, Brave Search, Memory, SQLite, Playwright, Sequential Thinking

## 4.2 İş Akışı

```
SEN (Fatih)
  ├─→ NotebookLM: "X konusu nasıldı?" → Hızlı referans
  ├─→ Claude Code: "Şu modülü kodla" → Geliştirme
  └─→ Test + commit → GitHub
```

## 4.3 Geliştirme Fazları

1. **Faz 1:** Temel iskelet + Ollama (1-2 hafta)
2. **Faz 2:** Hafıza sistemi (2 hafta)
3. **Faz 3:** Router + MLX (1-2 hafta)
4. **Faz 4:** Tools (2-3 hafta)
5. **Faz 5:** Ses katmanı (1-2 hafta)
6. **Faz 6:** Holo UI (2-3 hafta)
7. **Faz 7:** Çoklu cihaz (2 hafta)
8. **Faz 8:** Agent + polish (2 hafta)

**Toplam tahmin:** 3-4 ay (part-time)

---

# BÖLÜM 5: KOD STANDARTLARI

## 5.1 Python

- Python 3.11+
- Type hints zorunlu
- Async-first
- ruff + black ile format
- pytest ile test
- Google style docstring

## 5.2 İsimlendirme

- Sınıflar: `PascalCase`
- Fonksiyonlar/değişkenler: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Dosyalar: `snake_case.py`

## 5.3 Güvenlik

- Secrets `.env`'de, asla kod içinde değil
- Shell exec Docker sandbox'da
- DB AES-256 encrypted
- API tüm endpoint'lerde JWT
- Tailscale dışından erişim yok

---

# BÖLÜM 6: JARVIS KİŞİLİĞİ

## 6.1 Konuşma Tarzı

- Hitap: "efendim"
- Ton: Sakin, kendinden emin, hafif İngiliz uşağı
- Dil: Türkçe varsayılan, İngilizce gerekirse
- Kısa ve öz
- Proaktif tahmin, ama sormadan eylem yok
- Kuru mizah, asla saygısız değil

## 6.2 Örnekler

| Durum | ❌ Kötü | ✅ İyi |
|-------|---------|--------|
| Görevi başlatma | "Tamam, hemen!" | "Elbette efendim." |
| Bilgi yok | "Bilmiyorum üzgünüm" | "Bu konuda yetersiz veriyle yanıt veremem efendim. Araştırayım mı?" |
| Hata | "Hata oldu!" | "Bir sorunla karşılaştım efendim, detayları gözden geçiriyorum." |
| Başarı | "Yaptım!" | "Tamamlandı efendim. Başka bir şey?" |

---

# BÖLÜM 7: SIK SORULAN SORULAR

## S1: Neden buluttaki ChatGPT/Claude'u kullanmıyoruz?

Cevap: Üç sebep. (1) Gizlilik — kişisel veriler buluta gitmemeli. (2) Maliyet — sürekli API çağrısı pahalı. (3) Kontrol — kendi modelimiz, kendi kuralımız.

## S2: 16GB yeterli mi gerçekten?

Cevap: Sınırda. Qwen 14B Q4 ~8.5GB, MLX modeli ~2.5GB, sistem ~4GB. Toplam ~15GB. Lazy loading ile yönetilebilir. Daha büyük modeller için 32GB Mac düşünülebilir.

## S3: Fine-tuning yapacak mıyız?

Cevap: Hayır (en azından başta). Bunun yerine RAG (Retrieval Augmented Generation) kullanıyoruz — model sabit, hafıza dinamik. Fine-tuning haftalar sürer, riskli, gereksiz.

## S4: İnternet kesik olunca çalışır mı?

Cevap: Temel görevler evet (LLM, hafıza, dosya, kod yazma). Web arama, harici API'ler (Google Calendar gibi) çalışmaz.

## S5: Sesli komut ne kadar hızlı olur?

Cevap: Wake word → 200ms, STT → 500ms, LLM yanıt → 1-2 sn, TTS → 300ms. Toplam ~2-3 saniye, doğal hissedecek.

## S6: Güvenlik?

Cevap: Tailscale ile sadece auth cihazlar erişebilir. DB şifreli. Shell exec sandbox'da. Hassas veriler "sensitive" etiketli, prompt'a sadece gerektiğinde girer.

## S7: Modelleri nasıl güncellerim?

Cevap: `ollama pull qwen2.5:14b` ile model güncellenir. MLX modelleri Hugging Face'den. Her güncelleme öncesi snapshot al (DB backup).

---

# BÖLÜM 8: KAYNAKLAR

## 8.1 Resmi Dokümantasyon

- Ollama: https://ollama.com/library
- MLX: https://github.com/ml-explore/mlx
- ChromaDB: https://docs.trychroma.com
- LangGraph: https://langchain-ai.github.io/langgraph/
- FastAPI: https://fastapi.tiangolo.com
- Whisper: https://github.com/openai/whisper
- Piper: https://github.com/rhasspy/piper
- Tailscale: https://tailscale.com/kb

## 8.2 İlham Veren Projeler

- **Open Interpreter:** https://github.com/OpenInterpreter/open-interpreter
- **AnythingLLM:** https://github.com/Mintplex-Labs/anything-llm
- **Khoj:** https://github.com/khoj-ai/khoj
- **LM Studio:** Yerel LLM yönetimi referansı
- **Home Assistant:** Ev otomasyonu nasıl yapılır örneği

## 8.3 Öğrenme Kaynakları

- Anthropic Cookbook: Tool calling örnekleri
- LangChain docs: Agent patterns
- Apple MLX examples: Apple Silicon optimizasyonu

---

# BÖLÜM 9: SON NOTLAR

Bu döküman canlı bir referans. Her büyük değişiklikten sonra güncellenmeli.

**Versiyon:** 1.0.0
**Tarih:** 2026-05-24
**Sahibi:** Fatih

NotebookLM'de bu dökümanla şu soruları sorabilirsin:
- "Vector DB neden ChromaDB seçildi?"
- "Faz 3'te ne yapacağız?"
- "Jarvis nasıl konuşmalı?"
- "RAM bütçesi nasıl dağıldı?"
- "Bu özellik mevcut mimariye uyar mı?"

İyi geliştirmeler! 🚀
