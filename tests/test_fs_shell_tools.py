"""file_system ve shell_exec araçları için testler."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.tools.file_system import ListDirTool, ReadFileTool, WriteFileTool
from jarvis.tools.shell_exec import ShellExecTool

# ── file_system ──


async def test_write_then_read(tmp_path: Path) -> None:
    writer = WriteFileTool(str(tmp_path))
    reader = ReadFileTool(str(tmp_path))
    msg = await writer.run(path="notlar/a.txt", content="merhaba efendim")
    assert "Yazıldı" in msg
    assert await reader.run(path="notlar/a.txt") == "merhaba efendim"


async def test_read_missing_file(tmp_path: Path) -> None:
    reader = ReadFileTool(str(tmp_path))
    assert "bulunamadı" in await reader.run(path="yok.txt")


async def test_list_dir(tmp_path: Path) -> None:
    (tmp_path / "x.txt").write_text("1")
    (tmp_path / "sub").mkdir()
    listing = await ListDirTool(str(tmp_path)).run(path=".")
    assert "x.txt" in listing
    assert "sub/" in listing


async def test_path_escape_blocked(tmp_path: Path) -> None:
    reader = ReadFileTool(str(tmp_path))
    with pytest.raises(ValueError, match="dışına çıkılamaz"):
        await reader.run(path="../../etc/passwd")


async def test_write_escape_blocked(tmp_path: Path) -> None:
    writer = WriteFileTool(str(tmp_path))
    with pytest.raises(ValueError, match="dışına çıkılamaz"):
        await writer.run(path="../escape.txt", content="x")


# ── shell_exec ──


async def test_echo(tmp_path: Path) -> None:
    tool = ShellExecTool(str(tmp_path))
    out = await tool.run(command="echo merhaba")
    assert "merhaba" in out
    assert "çıkış kodu: 0" in out


async def test_allowlist_blocks_unknown(tmp_path: Path) -> None:
    tool = ShellExecTool(str(tmp_path), allowlist=frozenset({"echo"}))
    out = await tool.run(command="rm -rf /")
    assert "izin verilen komutlar arasında değil" in out


async def test_empty_command(tmp_path: Path) -> None:
    tool = ShellExecTool(str(tmp_path))
    assert "boş komut" in await tool.run(command="   ")


async def test_runs_in_workdir(tmp_path: Path) -> None:
    (tmp_path / "marker.txt").write_text("x")
    tool = ShellExecTool(str(tmp_path))
    out = await tool.run(command="ls")
    assert "marker.txt" in out


async def test_timeout(tmp_path: Path) -> None:
    tool = ShellExecTool(str(tmp_path), allowlist=None, timeout=0.5)
    out = await tool.run(command="sleep 5")
    assert "tamamlanmadı" in out


async def test_no_shell_injection(tmp_path: Path) -> None:
    # shell=False olduğundan ';' ve '|' özel karakter değil, echo'ya argüman olur.
    tool = ShellExecTool(str(tmp_path))
    out = await tool.run(command="echo a ; rm -rf x")
    assert "rm" in out  # echo argümanı olarak basıldı, çalıştırılmadı
    assert "çıkış kodu: 0" in out
