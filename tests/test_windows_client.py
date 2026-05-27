"""Windows/masaüstü istemci import smoke testi.

GUI görseli ve pencere örneklemesi bu sandbox'ta doğrulanamaz (Qt platform
plugin yok). Bunun yerine, izole bir alt süreçte modülün hatasız import
edildiği ve beklenen sınıfların tanımlı olduğu doğrulanır — bu, PyQt6 kodunun
söz dizimi/import/öznitelik açısından sağlam olduğunu kanıtlar. PyQt6'yı
torch/mlx ile aynı süreçte yüklemek native çökmeye yol açabildiğinden alt
süreç kullanılır. PyQt6 kurulu değilse atlanır.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("PyQt6") is None, reason="PyQt6 kurulu değil."
)

_MAIN_PATH = Path(__file__).resolve().parent.parent / "clients" / "windows" / "main.py"

_SCRIPT = f"""
import importlib.util

spec = importlib.util.spec_from_file_location("win_main", r"{_MAIN_PATH}")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert isinstance(mod.ChatWindow, type)
assert isinstance(mod.ChatWorker, type)
assert callable(mod.main)
print("IMPORT_OK")
"""


def test_module_imports_cleanly() -> None:
    result = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert "IMPORT_OK" in result.stdout, result.stderr
    assert result.returncode == 0, result.stderr
