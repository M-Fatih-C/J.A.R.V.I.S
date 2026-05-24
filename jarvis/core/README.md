# core/

Jarvis'in bilişsel çekirdeği.

- `orchestrator.py` — İstekleri uçtan uca yöneten ana koordinatör (FastAPI + AsyncIO).
- `router.py` — Niyet tespiti; isteği Fast Lane (MLX) veya Deep Think (Ollama) hattına yönlendirir.
- `agent.py` — LangGraph tabanlı ReAct agent; tool calling görevlerini yürütür.

> Faz 1'de bu klasör henüz boş; iskelet sonraki fazlarda dolacak.
