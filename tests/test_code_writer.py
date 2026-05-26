"""RunPythonTool (code_writer sandbox) testleri."""

from __future__ import annotations

from pathlib import Path

from jarvis.tools.code_writer import RunPythonTool


async def test_runs_and_captures_stdout(tmp_path: Path) -> None:
    tool = RunPythonTool(str(tmp_path))
    out = await tool.run(code="print(2 + 3)")
    assert "5" in out
    assert "çıkış kodu: 0" in out


async def test_nonzero_exit_on_error(tmp_path: Path) -> None:
    tool = RunPythonTool(str(tmp_path))
    out = await tool.run(code="raise ValueError('patlama')")
    assert "patlama" in out
    assert "çıkış kodu: 0" not in out


async def test_timeout(tmp_path: Path) -> None:
    tool = RunPythonTool(str(tmp_path), timeout=0.5)
    out = await tool.run(code="import time; time.sleep(5)")
    assert "tamamlanmadı" in out


async def test_runs_in_workdir(tmp_path: Path) -> None:
    tool = RunPythonTool(str(tmp_path))
    out = await tool.run(code="from pathlib import Path; Path('cikti.txt').write_text('ok')")
    assert "çıkış kodu: 0" in out
    assert (tmp_path / "cikti.txt").read_text() == "ok"


async def test_temp_script_cleaned_up(tmp_path: Path) -> None:
    tool = RunPythonTool(str(tmp_path))
    await tool.run(code="print('hi')")
    # Geçici .py dosyaları temizlenmeli (yalnızca kullanıcı çıktısı kalır).
    leftover = list(tmp_path.glob("*.py"))
    assert leftover == []


async def test_output_truncation(tmp_path: Path) -> None:
    tool = RunPythonTool(str(tmp_path))
    out = await tool.run(code="print('a' * 20000)")
    assert "kırpıldı" in out
