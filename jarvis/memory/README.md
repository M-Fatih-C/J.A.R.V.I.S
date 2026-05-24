# memory/

Üç katmanlı hafıza sistemi (Faz 2).

- `short_term.py` — Redis tabanlı kısa süreli bağlam (konuşma penceresi).
- `vector_store.py` — ChromaDB + `nomic-embed-text` ile anlamsal hafıza.
- `profile.py` — SQLite (AES-256 şifreli) kullanıcı profili.
- `learning.py` — Arka plan worker; otomatik özetleme ve pasif öğrenme.

> Faz 1'de boş; Faz 2'de implemente edilecek.
