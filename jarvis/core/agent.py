"""Agent motoru — LangGraph ReAct agent'ı araçlarla birleştirir.

ChatOllama (Qwen 2.5, native tool-calling) + LangGraph ``create_react_agent``
kullanır. Araçlar :class:`ToolRegistry` üzerinden sağlanır.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from jarvis.config import settings
from jarvis.tools.base import ToolRegistry
from jarvis.tools.calendar_tool import CreateEventTool, ListEventsTool
from jarvis.tools.code_writer import RunPythonTool
from jarvis.tools.email_tool import SendEmailTool
from jarvis.tools.file_system import ListDirTool, ReadFileTool, WriteFileTool
from jarvis.tools.research import FetchUrlTool
from jarvis.tools.shell_exec import ShellExecTool
from jarvis.tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = (
    "Sen Jarvis'sin: sakin, kendinden emin bir kişisel asistan. Kullanıcıya "
    "'efendim' diye hitap edersin. Gerektiğinde sağlanan araçları kullanarak "
    "görevleri yerine getirirsin; araç gerekmiyorsa doğrudan yanıt verirsin. "
    "Yanıtların kısa ve öz olsun."
)


def build_default_registry(workdir: str) -> ToolRegistry:
    """Varsayılan araç setini içeren bir :class:`ToolRegistry` üretir.

    file_system, shell_exec, web_search ve fetch_url tam çalışır; email ve
    calendar iskelet (yapılandırılmamış) olarak kaydedilir.

    Args:
        workdir: Dosya/shell araçlarının hapsedileceği çalışma dizini.

    Returns:
        Doldurulmuş kayıt defteri.
    """
    registry = ToolRegistry()
    for tool in (
        ReadFileTool(workdir),
        WriteFileTool(workdir),
        ListDirTool(workdir),
        ShellExecTool(workdir),
        RunPythonTool(workdir),
        WebSearchTool(),
        FetchUrlTool(),
        SendEmailTool(),
        CreateEventTool(),
        ListEventsTool(),
    ):
        registry.register(tool)
    return registry


class JarvisAgent:
    """Araç kullanabilen ReAct agent sarmalayıcısı."""

    def __init__(
        self,
        registry: ToolRegistry,
        model: str | None = None,
        base_url: str | None = None,
        system_prompt: str = AGENT_SYSTEM_PROMPT,
    ) -> None:
        """JarvisAgent'ı başlatır.

        Args:
            registry: Araç kayıt defteri.
            model: Ollama sohbet modeli; ``None`` ise ayarlardaki varsayılan.
            base_url: Ollama adresi; ``None`` ise ayarlardaki değer.
            system_prompt: Agent sistem prompt'u.
        """
        self.registry = registry
        self._llm = ChatOllama(
            model=model or settings.ollama_default_model,
            base_url=base_url or settings.ollama_url,
        )
        self._agent = create_agent(
            self._llm,
            registry.to_langchain(),
            system_prompt=system_prompt,
        )

    async def run(self, message: str) -> str:
        """Bir kullanıcı isteğini agent ile (gerekirse araç çağırarak) işler.

        Args:
            message: Kullanıcı mesajı.

        Returns:
            Agent'ın ürettiği son yanıt metni.
        """
        logger.info("Agent çalışıyor: %r", message)
        result: dict[str, Any] = await self._agent.ainvoke(
            cast(Any, {"messages": [("user", message)]})
        )
        messages = result.get("messages", [])
        if not messages:
            return ""
        content = messages[-1].content
        return content if isinstance(content, str) else str(content)
