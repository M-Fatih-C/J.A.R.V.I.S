#!/usr/bin/env bash
# Jarvis API'yi geliştirme modunda başlatır.
set -euo pipefail

cd "$(dirname "$0")/.."

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

echo "🔍 Ollama kontrol ediliyor: ${OLLAMA_URL}"
if curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    echo "✅ Ollama erişilebilir."
else
    echo "⚠️  Ollama'ya ulaşılamadı. 'ollama serve' çalışıyor mu?"
    echo "    API yine de başlayacak ancak /chat istekleri başarısız olabilir."
fi

echo "🚀 Jarvis API başlatılıyor (reload mode)..."
exec uv run uvicorn jarvis.api.main:app --reload --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
