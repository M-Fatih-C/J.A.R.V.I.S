#!/usr/bin/env bash
# Jarvis için Tailscale kurulumuna yardımcı script (macOS sunucu).
# Cihazlar (iPhone, Windows) aynı tailnet'e katılınca Mac sunucusuna güvenli
# erişir. API'yi 0.0.0.0:8000'de dinletin; Tailscale IP/host üzerinden bağlanın.
set -euo pipefail

echo "═══════════════════════════════════════════"
echo "  Jarvis · Tailscale kurulum yardımcısı"
echo "═══════════════════════════════════════════"

if ! command -v tailscale >/dev/null 2>&1; then
    echo "⬇️  Tailscale bulunamadı. Kurulum:"
    echo "    brew install --cask tailscale"
    echo "    (veya https://tailscale.com/download)"
    exit 1
fi
echo "✅ tailscale mevcut: $(tailscale version | head -1)"

echo "🔑 Tailscale'e giriş yapın (tarayıcı açılır):"
echo "    sudo tailscale up"
echo

echo "ℹ️  Bu makinenin tailnet adresi:"
tailscale ip -4 2>/dev/null || echo "    (önce 'sudo tailscale up' çalıştırın)"
echo
echo "Sonraki adımlar:"
echo "  1) API'yi tüm arayüzlerde başlatın:  HOST=0.0.0.0 ./scripts/run_dev.sh"
echo "  2) .env'de AUTH_ENABLED=true ve güçlü bir DEVICE_KEY ayarlayın."
echo "  3) iPhone/Windows'ta Tailscale'i kurup aynı hesapla giriş yapın."
echo "  4) İstemcilerde API adresi olarak Tailscale host'unu kullanın:"
echo "     http://<bu-makinenin-tailscale-adı>.ts.net:8000"
echo "═══════════════════════════════════════════"
