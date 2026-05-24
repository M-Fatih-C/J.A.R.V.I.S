# models/

LLM client'ları ve ortak soyutlamalar.

- `base.py` — `LLMClient` soyut taban sınıfı + `ChatMessage` / `ChatResponse` Pydantic modelleri.
- `ollama_client.py` — Ollama HTTP API'si üzerinden async sohbet (Deep Think hattı, Qwen 2.5 14B).
- `mlx_client.py` — (Faz 3) Apple MLX ile hızlı yerel çıkarım (Fast Lane).

Tüm client'lar `LLMClient` arayüzünü uygular: `chat`, `chat_stream`, `list_models`, `health_check`.
