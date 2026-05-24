#!/usr/bin/env bash
# Jarvis geliştirme ortamını kurar (uv tabanlı).
set -euo pipefail

cd "$(dirname "$0")/.."

echo "═══════════════════════════════════════════"
echo "  Jarvis kurulum scripti"
echo "═══════════════════════════════════════════"

# 1) uv kontrolü
if ! command -v uv >/dev/null 2>&1; then
    echo "❌ uv bulunamadı. Kurulum: https://docs.astral.sh/uv/"
    echo "   brew install uv"
    exit 1
fi
echo "✅ uv: $(uv --version)"

# 2) Sanal ortam + bağımlılıklar
echo "📦 Bağımlılıklar kuruluyor (dev dahil)..."
uv sync --extra dev

# 3) .env dosyası
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 .env oluşturuldu (.env.example'dan). Sırları düzenlemeyi unutmayın."
else
    echo "📝 .env zaten mevcut, dokunulmadı."
fi

# 4) data klasörü
mkdir -p data/chroma data/redis
echo "📁 data/ klasörleri hazır."

# 5) Ollama kontrolü
if command -v ollama >/dev/null 2>&1; then
    echo "✅ ollama kurulu: $(ollama --version 2>/dev/null | head -1)"
    MODEL="${OLLAMA_DEFAULT_MODEL:-qwen2.5:14b}"
    if ollama list 2>/dev/null | grep -q "${MODEL%%:*}"; then
        echo "✅ Model mevcut: ${MODEL}"
    else
        echo "⬇️  Model indiriliyor: ${MODEL} (~10GB, birkaç dakika)..."
        ollama pull "${MODEL}"
    fi
else
    echo "⚠️  ollama bulunamadı. Kurulum: brew install ollama"
    echo "    Ardından: ollama serve && ollama pull qwen2.5:14b"
fi

echo "═══════════════════════════════════════════"
echo "✅ Kurulum tamam. Servisleri başlatmak için:"
echo "   docker compose up -d        # Redis + ChromaDB"
echo "   ./scripts/run_dev.sh        # API"
echo "═══════════════════════════════════════════"
