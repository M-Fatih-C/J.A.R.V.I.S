# config/

Uygulama yapılandırması.

- `settings.py` — `pydantic-settings` tabanlı, `.env`'den okuyan merkezî ayarlar. `settings` singleton'ı buradan import edilir.
- `prompts/` — Jarvis kişilik ve sistem prompt şablonları.

Yeni bir ayar eklerken hem `Settings` sınıfına hem de `.env.example`'a ekleyin.
