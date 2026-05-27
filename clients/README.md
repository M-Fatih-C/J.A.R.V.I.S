# clients/ — Çoklu Cihaz İstemcileri

Jarvis sunucusu (Mac M4) API'yi açar; istemciler **Tailscale VPN** üzerinden,
**JWT** ile kimlik doğrulayarak bağlanır.

## Mimari
```
iPhone (SwiftUI) ┐
Windows/Mac (PyQt6) ┼─ Tailscale VPN ─→ Mac sunucu :8000 (FastAPI)
Holo UI (tarayıcı) ┘        (JWT auth)        └─ Orchestrator/Agent
```

## Kimlik doğrulama akışı
1. İstemci `POST /auth/token` `{ "device_key": "<sır>" }` → `{ access_token }`.
2. Korunan uç noktalara `Authorization: Bearer <token>` ile erişilir
   (`/chat`, `/agent`, `/ws?token=<token>`).
3. `AUTH_ENABLED=false` ise auth atlanır (yalnızca yerel geliştirme).

## İstemciler
- **`windows/`** — PyQt6 masaüstü istemcisi (macOS/Windows/Linux).
  ```bash
  JARVIS_API=http://<host>:8000 JARVIS_DEVICE_KEY=<sır> \
      uv run --extra windows python clients/windows/main.py
  ```
- **`ios/`** — SwiftUI iskelet (Xcode ile derlenir; bkz. `ios/README.md`).
- **Holo UI** — `ui/` (tarayıcı, ayrı README).

Paylaşılan Python SDK: `jarvis/client.py` (`JarvisClient`).

## Tailscale
`./scripts/setup_tailscale.sh` rehberini izleyin. Özet:
- Sunucuda `sudo tailscale up`, API'yi `HOST=0.0.0.0` ile başlatın.
- Her cihaza Tailscale kurup aynı tailnet'e katın.
- İstemcilerde adres: `http://<sunucu>.ts.net:8000`.
