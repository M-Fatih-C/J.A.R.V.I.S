"""Agent ve tool kayıt defteri testleri.

Gerçek agent çalıştırması (Qwen + tool-calling) yavaştır; JARVIS_E2E=1 ile açılır.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from jarvis.core.agent import JarvisAgent, build_default_registry

EXPECTED_TOOLS = {
    "read_file",
    "write_file",
    "list_dir",
    "shell_exec",
    "web_search",
    "fetch_url",
    "send_email",
    "create_calendar_event",
    "list_calendar_events",
}


def test_registry_has_all_tools(tmp_path: Path) -> None:
    registry = build_default_registry(str(tmp_path))
    assert set(registry.names()) == EXPECTED_TOOLS


def test_registry_to_langchain(tmp_path: Path) -> None:
    registry = build_default_registry(str(tmp_path))
    lc_tools = registry.to_langchain()
    assert len(lc_tools) == len(EXPECTED_TOOLS)
    names = {t.name for t in lc_tools}
    assert names == EXPECTED_TOOLS
    # Her LangChain aracının args_schema'sı olmalı.
    assert all(t.args_schema is not None for t in lc_tools)


def test_agent_builds(tmp_path: Path) -> None:
    registry = build_default_registry(str(tmp_path))
    agent = JarvisAgent(registry)
    assert agent._agent is not None
    assert set(agent.registry.names()) == EXPECTED_TOOLS


@pytest.mark.skipif(
    "JARVIS_E2E" not in os.environ,
    reason="Gerçek agent testi atlandı (JARVIS_E2E=1 ile etkinleşir).",
)
async def test_agent_uses_tool(tmp_path: Path) -> None:
    """Agent, dosya yazma isteğini araç çağırarak gerçekleştirir."""
    registry = build_default_registry(str(tmp_path))
    agent = JarvisAgent(registry)
    await agent.run(
        "merhaba.txt adlı dosyaya 'selam efendim' yaz. Sadece write_file aracını kullan."
    )
    written = tmp_path / "merhaba.txt"
    assert written.exists()
    assert "selam" in written.read_text().lower()
