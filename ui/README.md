# ui/ — Jarvis Holo UI

React + TypeScript + Three.js (react-three-fiber) ile holografik arayüz.

## Çalıştırma

```bash
cd ui
npm install
npm run dev        # http://localhost:5173 (Vite)
```

Vite dev sunucusu `/ws` ve REST yollarını `localhost:8000`'deki Jarvis API'sine
proxy'ler. Önce backend'i başlatın: `./scripts/run_dev.sh`.

## Komutlar
- `npm run dev` — geliştirme sunucusu
- `npm run build` — tsc tip kontrolü + üretim derlemesi (`dist/`)
- `npm run typecheck` — yalnızca tip kontrolü

## Yapı
```
src/
├── main.tsx               # React girişi
├── App.tsx                # Düzen: Sahne + overlay
├── store.ts               # zustand durum (status, mesajlar, ayarlar)
├── types.ts
├── hooks/useJarvisSocket.ts   # /ws bağlantısı (otomatik reconnect)
└── components/
    ├── Scene.tsx          # R3F Canvas (çekirdek + dalga + parçacıklar)
    ├── JarvisCore.tsx     # Duruma tepki veren bozulan küre
    ├── VoiceWave.tsx      # Ses çubukları halkası
    ├── StatusIndicator.tsx
    ├── ChatPanel.tsx
    └── SettingsPanel.tsx  # WS adresi, oturum, vurgu rengi
```

## Protokol
İstemci `{ "message": "...", "session_id": "ui" }` gönderir; sunucu sırayla
`status(thinking)` → `response` → `status(idle)` event'leri yayınlar.
Çekirdek ve ses dalgası bu duruma göre animasyon değiştirir.
