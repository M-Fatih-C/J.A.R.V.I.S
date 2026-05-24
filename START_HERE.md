# 🚀 Jarvis Başlangıç Paketi — Kullanım Rehberi

> Bu paketle ne yapacağını adım adım anlatıyorum. 30 dakika içinde
> Claude Code'la geliştirmeye başlayabilirsin.

---

## 📦 Paket İçeriği

```
jarvis-starter/
├── CLAUDE.md                  # Claude Code için ana bağlam
├── README.md                  # Proje tanıtımı (GitHub'da görünecek)
├── CLAUDE_CODE_COMMANDS.md    # Adım adım komut rehberi
├── NOTEBOOKLM_MASTER.md       # NotebookLM için master döküman
├── START_HERE.md              # Bu dosya
└── scripts/
    └── setup_mcp.sh           # MCP sunucu kurulumu
```

---

## 🎯 Hangi Dosya Ne İşe Yarar?

| Dosya | Nereye? | Ne için? |
|-------|---------|----------|
| `CLAUDE.md` | Proje root'una | Claude Code her açılışta okur, mimariyi bilir |
| `README.md` | Proje root'una | GitHub'da ana sayfa |
| `CLAUDE_CODE_COMMANDS.md` | Local (sende kalsın) | Sırayla Claude Code'a yapıştır |
| `NOTEBOOKLM_MASTER.md` | NotebookLM'e yükle | Proje "beyni", hızlı referans |
| `scripts/setup_mcp.sh` | Proje `scripts/` klasörü | MCP'leri otomatik kurar |

---

## ⏱️ 30 Dakikalık Başlangıç

### Adım 1: Ön Hazırlık (5 dk)

Mac'te şunları kur (yoksa):

```bash
# Homebrew (yoksa)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Node.js (Claude Code için)
brew install node

# Python 3.11+
brew install python@3.11

# Ollama
brew install ollama

# Git
brew install git

# Claude Code
npm install -g @anthropic-ai/claude-code
```

### Adım 2: Ollama'yı Hazırla (10 dk)

```bash
# Ollama servisini başlat
ollama serve &

# Modelleri indir (bu birkaç dakika sürer, ~10GB)
ollama pull qwen2.5:14b
ollama pull nomic-embed-text  # embedding için

# Test et
ollama run qwen2.5:14b "Merhaba, kimsin?"
```

### Adım 3: Projeyi Başlat (5 dk)

```bash
# Projeyi oluştur
mkdir -p ~/projects/jarvis
cd ~/projects/jarvis

# Bu paketteki dosyaları kopyala
cp /path/to/CLAUDE.md .
cp /path/to/README.md .
mkdir scripts
cp /path/to/scripts/setup_mcp.sh scripts/
chmod +x scripts/setup_mcp.sh

# Git init
git init
echo "venv/
__pycache__/
.env
*.pyc
.DS_Store
node_modules/
data/" > .gitignore

# İlk commit
git add .
git commit -m "chore: initial project setup with architecture context"
```

### Adım 4: MCP'leri Kur (5 dk)

```bash
# Önce environment variable'ları ayarla
export BRAVE_API_KEY="..."  # https://brave.com/search/api/ adresinden al
export GITHUB_TOKEN="ghp_..."  # GitHub Personal Access Token

# Script'i çalıştır
./scripts/setup_mcp.sh

# Doğrula
claude mcp list
```

### Adım 5: NotebookLM Hazırlığı (5 dk)

1. https://notebooklm.google.com adresine git
2. "New notebook" oluştur, adı: "Jarvis Project"
3. `NOTEBOOKLM_MASTER.md` dosyasını yükle
4. Bu paketteki diğer dosyaları da yükle (CLAUDE.md, README.md)
5. Bu konuşmanın PDF'ini de yükle (Claude'dan indirebilirsin)

Test sorusu: NotebookLM'e sor: "Faz 1'de ne yapacağız?"

### Adım 6: Claude Code'u Başlat

```bash
cd ~/projects/jarvis
claude
```

İlk komutu yapıştır (`CLAUDE_CODE_COMMANDS.md` → KOMUT 1).

---

## 🔄 Günlük İş Akışı

### Sabah Rutini (5 dk)

1. NotebookLM aç, dünkü ilerlemeyi sor: "Son durumum neydi?"
2. Bugünkü görevi belirle
3. Claude Code aç (`cd ~/projects/jarvis && claude`)

### Geliştirme Döngüsü

```
┌─────────────────────────────────────┐
│  1. NotebookLM'e danış               │
│     "X özelliği nasıl olmalı?"      │
│              ↓                       │
│  2. Claude Code'a komut ver          │
│     "Şunu kodla..."                  │
│              ↓                       │
│  3. Plan onaylayınca koda dökmesini  │
│     iste                             │
│              ↓                       │
│  4. Test et                          │
│              ↓                       │
│  5. Commit                           │
│              ↓                       │
│  6. NotebookLM'e güncel durumu       │
│     yükle (önemli değişiklikler)     │
└─────────────────────────────────────┘
```

### Akşam Rutini (5 dk)

1. `git push` ile commit'leri gönder
2. CLAUDE.md'deki ilerlemeyi güncelle
3. Yarının görevini not al

---

## 💡 Pro İpuçları

### Claude Code'u Daha Verimli Kullanmak

**1. Plan Mode kullan**
Karmaşık görevlerden önce: `/plan` komutu ile önce planlatır, sonra kodlatırsın.

**2. Slash komutları**
- `/clear` — context temizle
- `/cost` — token kullanımı
- `/mcp` — bağlı MCP'leri gör

**3. Dosya referansı**
`@dosya.py` yazınca o dosyayı context'e ekler.

**4. Skill mention**
Anthropic'in built-in skill'lerini kullan: docx, pdf, xlsx skills'leri proje dökümanları için.

### NotebookLM'i Daha Verimli Kullanmak

**1. Düzenli güncelle**
Her büyük değişiklikten sonra güncel dosyaları yükle.

**2. Podcast özelliği**
Uzun yürüyüş/seyahat: NotebookLM'in podcast özelliğiyle projeyi "dinle".

**3. Spesifik sorular sor**
❌ "Nasıl gidiyor?"
✅ "Faz 2'deki vector store implementasyonunda hangi metodları yazmalıyım?"

**4. Mind map oluştur**
NotebookLM mind map çıkarabiliyor, mimari için kullanışlı.

---

## 🆘 Sorun Giderme

### "Ollama bağlantı hatası"
```bash
# Ollama çalışıyor mu?
curl http://localhost:11434/api/tags

# Çalışmıyorsa:
ollama serve
```

### "Out of memory"
- Daha küçük model: `ollama pull qwen2.5:7b`
- Diğer uygulamaları kapat
- Activity Monitor ile RAM kullanımını izle

### "Claude Code çalışmıyor"
```bash
# Versiyonu kontrol et
claude --version

# Güncelle
npm update -g @anthropic-ai/claude-code

# Yardım
claude --help
```

### "MCP server connect failed"
```bash
# Yeniden başlat
claude mcp remove <server-name>
claude mcp add <server-name> ...
```

---

## 📅 İlk 4 Hafta Roadmap

### Hafta 1: Faz 1 — İskelet
- [ ] Proje yapısı
- [ ] Ollama client
- [ ] FastAPI iskelet
- [ ] İlk uçtan-uca chat

### Hafta 2: Faz 2 (Başlangıç) — Hafıza
- [ ] Short-term memory (Redis)
- [ ] Vector store (ChromaDB)
- [ ] Basic profile DB

### Hafta 3: Faz 2 (Devam) + Faz 3 (Başlangıç)
- [ ] Learning engine
- [ ] MLX entegrasyonu
- [ ] Model router

### Hafta 4: Faz 4 — İlk Tools
- [ ] Tool calling altyapısı
- [ ] Web search tool
- [ ] Demo: "Bugünün AI haberlerini özetle"

---

## 🎓 Sonraki Adımlar

İlk demo çalıştığında (Hafta 4 sonu):

1. Aileye/arkadaşlara göster — feedback al
2. NotebookLM'i güncelle, lessons learned ekle
3. v0.2 planlaması yap
4. Faz 5'e (Ses) geç

---

## 📞 Yardım Almak

Takıldığında:
1. **NotebookLM'e sor** — Genel mimari/karar soruları
2. **Claude Code'a sor** — Spesifik kod hataları
3. **Claude.ai** — Yeni özellik tasarımı, derin teknik tartışmalar
4. **Discord/Reddit** — Topluluk: r/LocalLLaMA, Ollama Discord

---

**Hadi başlayalım! Mac'te terminal aç, ilk komuttan başla. 🚀**

İyi şanslar Fatih!
