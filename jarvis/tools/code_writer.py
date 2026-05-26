"""Kod çalıştırma aracı — Python kodunu guardrail'lı sandbox'ta yürütür.

Güvenlik: kod geçici bir dosyaya yazılır ve çalışma dizinine hapsedilmiş bir
subprocess'te, zaman aşımı ve çıktı limitiyle çalıştırılır. Bu tam izolasyon
DEĞİLDİR (ağ/dosya erişimi mümkündür); yerel kişisel asistan için guardrail
sağlar. Daha güçlü izolasyon için ileride Docker sandbox eklenebilir.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from jarvis.tools.base import Tool

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
MAX_OUTPUT_CHARS = 10_000


class RunPythonArgs(BaseModel):
    code: str = Field(description="Çalıştırılacak Python kodu")


class RunPythonTool(Tool):
    """Python kodunu guardrail'lı bir alt süreçte çalıştırır ve çıktısını döndürür."""

    name = "run_python"
    description = (
        "Verilen Python kodunu çalıştırır ve birleşik stdout/stderr çıktısını "
        "döndürür. Hesaplama, veri işleme veya kod doğrulama için kullanılır."
    )
    args_schema = RunPythonArgs

    def __init__(
        self,
        workdir: str,
        timeout: float = DEFAULT_TIMEOUT,
        python_executable: str | None = None,
    ) -> None:
        """RunPythonTool'u başlatır.

        Args:
            workdir: Kodun çalışacağı (ve geçici dosyanın yazılacağı) dizin.
            timeout: Çalıştırma zaman aşımı (saniye).
            python_executable: Kullanılacak Python yorumlayıcısı; ``None`` ise
                mevcut yorumlayıcı (``sys.executable``).
        """
        self.workdir = Path(workdir).resolve()
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.python = python_executable or sys.executable

    async def run(self, **kwargs: Any) -> str:
        args = RunPythonArgs(**kwargs)

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=self.workdir,
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(args.code)
            script_path = Path(tmp.name)

        logger.info("Python çalıştırılıyor: %s (cwd=%s)", script_path.name, self.workdir)
        try:
            proc = await asyncio.create_subprocess_exec(
                self.python,
                str(script_path),
                cwd=str(self.workdir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            try:
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            except TimeoutError:
                proc.kill()
                await proc.wait()
                return f"Hata: kod {self.timeout:.0f} saniyede tamamlanmadı (sonlandırıldı)"
        finally:
            await asyncio.to_thread(script_path.unlink, missing_ok=True)

        output = stdout.decode("utf-8", errors="replace")
        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "\n... (çıktı kırpıldı)"
        return (
            f"[çıkış kodu: {proc.returncode}]\n{output}"
            if output.strip()
            else f"[çıkış kodu: {proc.returncode}] (çıktı yok)"
        )
