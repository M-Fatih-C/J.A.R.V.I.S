"""Shell exec aracı — subprocess (shell=False) + guardrail'lar.

Güvenlik: ``shell=False`` (boru/yönlendirme/enjeksiyon yok), komut allowlist,
zaman aşımı, çalışma dizini hapsi ve çıktı uzunluğu limiti.
"""

from __future__ import annotations

import asyncio
import logging
import shlex
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from jarvis.tools.base import Tool

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
MAX_OUTPUT_CHARS = 10_000

# LLM'in çağırabileceği makul, çoğunlukla okuma ağırlıklı varsayılan komutlar.
DEFAULT_ALLOWED: frozenset[str] = frozenset(
    {
        "ls",
        "cat",
        "echo",
        "pwd",
        "head",
        "tail",
        "wc",
        "grep",
        "find",
        "date",
        "whoami",
        "uname",
        "df",
        "du",
        "git",
        "python3",
        "python",
        "uv",
        "pip",
        "which",
        "tree",
        "sort",
        "uniq",
        "diff",
    }
)


class ShellExecArgs(BaseModel):
    command: str = Field(description="Çalıştırılacak shell komutu (tek satır)")


class ShellExecTool(Tool):
    """Komutları güvenli biçimde (sandbox'sız ama guardrail'lı) çalıştırır."""

    name = "shell_exec"
    description = (
        "Bir shell komutu çalıştırır ve çıktısını döndürür. Boru (|), "
        "yönlendirme (>) ve zincirleme (&&) DESTEKLENMEZ; tek bir komut verin."
    )
    args_schema = ShellExecArgs

    def __init__(
        self,
        workdir: str,
        allowlist: frozenset[str] | None = DEFAULT_ALLOWED,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """ShellExecTool'u başlatır.

        Args:
            workdir: Komutların çalışacağı dizin.
            allowlist: İzin verilen program adları; ``None`` ise tümüne izin verilir.
            timeout: Komut zaman aşımı (saniye).
        """
        self.workdir = Path(workdir).resolve()
        self.allowlist = allowlist
        self.timeout = timeout

    async def run(self, **kwargs: Any) -> str:
        args = ShellExecArgs(**kwargs)
        try:
            argv = shlex.split(args.command)
        except ValueError as exc:
            return f"Hata: komut ayrıştırılamadı: {exc}"
        if not argv:
            return "Hata: boş komut"

        program = argv[0]
        if self.allowlist is not None and program not in self.allowlist:
            return (
                f"Hata: '{program}' izin verilen komutlar arasında değil. "
                f"İzinli: {', '.join(sorted(self.allowlist))}"
            )

        logger.info("Shell exec: %s (cwd=%s)", argv, self.workdir)
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                cwd=str(self.workdir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            return f"Hata: komut bulunamadı: {program}"

        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return f"Hata: komut {self.timeout:.0f} saniyede tamamlanmadı (sonlandırıldı)"

        output = stdout.decode("utf-8", errors="replace")
        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "\n... (çıktı kırpıldı)"
        return (
            f"[çıkış kodu: {proc.returncode}]\n{output}"
            if output.strip()
            else f"[çıkış kodu: {proc.returncode}] (çıktı yok)"
        )
