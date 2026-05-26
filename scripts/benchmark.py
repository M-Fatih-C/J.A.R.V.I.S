#!/usr/bin/env python
"""Fast Lane (MLX) ile Deep Think (Ollama) gecikme/throughput karşılaştırması.

Kullanım:
    uv run python scripts/benchmark.py
    uv run python scripts/benchmark.py --prompt "Merhaba" --iterations 3

Ollama modeli yüklü değilse o kısım atlanır.
"""

from __future__ import annotations

import argparse
import asyncio
import time

from jarvis.config import settings
from jarvis.models import ChatMessage, MLXClient, OllamaClient
from jarvis.models.base import LLMClient


async def _bench(client: LLMClient, prompt: str, iterations: int) -> dict[str, float]:
    """Bir client'ı verilen prompt ile ölçer.

    Returns:
        Ortalama gecikme (ms), ortalama token, ort. token/sn istatistikleri.
    """
    messages = [ChatMessage(role="user", content=prompt)]
    latencies: list[float] = []
    token_counts: list[int] = []
    for _ in range(iterations):
        start = time.perf_counter()
        resp = await client.chat(messages)
        latencies.append((time.perf_counter() - start) * 1000)
        token_counts.append(resp.tokens or 0)

    avg_latency = sum(latencies) / len(latencies)
    avg_tokens = sum(token_counts) / len(token_counts)
    tok_per_sec = (avg_tokens / (avg_latency / 1000)) if avg_latency else 0.0
    return {
        "avg_latency_ms": avg_latency,
        "avg_tokens": avg_tokens,
        "tokens_per_sec": tok_per_sec,
    }


def _print_row(name: str, stats: dict[str, float]) -> None:
    print(
        f"{name:<14} | {stats['avg_latency_ms']:>10.0f} ms "
        f"| {stats['avg_tokens']:>7.0f} tok "
        f"| {stats['tokens_per_sec']:>7.1f} tok/s"
    )


async def main(prompt: str, iterations: int) -> None:
    print(f"\nPrompt: {prompt!r}  ·  iterations: {iterations}\n")
    print(f"{'Lane':<14} | {'Latency':>13} | {'Tokens':>11} | {'Throughput':>11}")
    print("-" * 60)

    # Fast Lane — MLX
    mlx = MLXClient()
    print("MLX yükleniyor (lazy)...", flush=True)
    mlx_stats = await _bench(mlx, prompt, iterations)
    _print_row("FAST (MLX)", mlx_stats)
    mlx.unload()

    # Deep Think — Ollama (model varsa)
    ollama = OllamaClient(base_url=settings.ollama_url, default_model=settings.ollama_default_model)
    target = settings.ollama_default_model.split(":")[0]
    models = await ollama.list_models() if await ollama.health_check() else []
    if any(m.split(":")[0] == target for m in models):
        ollama_stats = await _bench(ollama, prompt, iterations)
        _print_row("DEEP (Ollama)", ollama_stats)
    else:
        print(f"DEEP (Ollama)  | atlandı — '{settings.ollama_default_model}' " "modeli yüklü değil")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jarvis MLX vs Ollama benchmark")
    parser.add_argument("--prompt", default="Merhaba, bugün hava nasıl?")
    parser.add_argument("--iterations", type=int, default=3)
    args = parser.parse_args()
    asyncio.run(main(args.prompt, args.iterations))
