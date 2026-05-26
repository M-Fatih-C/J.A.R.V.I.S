"""Dosya sistemi araçları — kök dizine hapsedilmiş oku/yaz/listele."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from jarvis.tools.base import Tool

MAX_READ_CHARS = 20_000


class _Confined:
    """Verilen kök dizine hapseden yol çözücü (``..`` ile kaçışı engeller)."""

    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()

    def resolve(self, rel: str) -> Path:
        """Göreli yolu kök içinde güvenle çözer.

        Args:
            rel: Köke göre yol.

        Returns:
            Çözülmüş mutlak yol.

        Raises:
            ValueError: Yol kök dizinin dışına çıkıyorsa.
        """
        target = (self.root / rel).resolve()
        if target != self.root and self.root not in target.parents:
            raise ValueError(f"Kök dizin dışına çıkılamaz: {rel}")
        return target


class ReadFileArgs(BaseModel):
    path: str = Field(description="Köke göre okunacak dosya yolu")


class WriteFileArgs(BaseModel):
    path: str = Field(description="Köke göre yazılacak dosya yolu")
    content: str = Field(description="Dosyaya yazılacak içerik")


class ListDirArgs(BaseModel):
    path: str = Field(default=".", description="Köke göre listelenecek dizin")


class ReadFileTool(Tool):
    """Kök dizin içindeki bir dosyanın metin içeriğini okur."""

    name = "read_file"
    description = (
        "Belirtilen dosyanın metin içeriğini okur. Yol, çalışma kök dizinine " "görelidir."
    )
    args_schema = ReadFileArgs

    def __init__(self, root: str) -> None:
        self._fs = _Confined(root)

    async def run(self, **kwargs: Any) -> str:
        args = ReadFileArgs(**kwargs)
        target = self._fs.resolve(args.path)
        if not target.is_file():
            return f"Hata: dosya bulunamadı: {args.path}"
        text = target.read_text(encoding="utf-8", errors="replace")
        if len(text) > MAX_READ_CHARS:
            return text[:MAX_READ_CHARS] + "\n... (kırpıldı)"
        return text


class WriteFileTool(Tool):
    """Kök dizin içindeki bir dosyaya metin yazar (üst dizinleri oluşturur)."""

    name = "write_file"
    description = (
        "Belirtilen dosyaya metin içeriği yazar (varsa üzerine yazar). Yol, "
        "çalışma kök dizinine görelidir."
    )
    args_schema = WriteFileArgs

    def __init__(self, root: str) -> None:
        self._fs = _Confined(root)

    async def run(self, **kwargs: Any) -> str:
        args = WriteFileArgs(**kwargs)
        target = self._fs.resolve(args.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(args.content, encoding="utf-8")
        return f"Yazıldı: {args.path} ({len(args.content)} karakter)"


class ListDirTool(Tool):
    """Kök dizin içindeki bir dizinin içeriğini listeler."""

    name = "list_dir"
    description = (
        "Belirtilen dizindeki dosya ve klasörleri listeler. Yol, çalışma kök " "dizinine görelidir."
    )
    args_schema = ListDirArgs

    def __init__(self, root: str) -> None:
        self._fs = _Confined(root)

    async def run(self, **kwargs: Any) -> str:
        args = ListDirArgs(**kwargs)
        target = self._fs.resolve(args.path)
        if not target.is_dir():
            return f"Hata: dizin bulunamadı: {args.path}"
        entries = sorted(f"{p.name}/" if p.is_dir() else p.name for p in target.iterdir())
        return "\n".join(entries) if entries else "(boş dizin)"
