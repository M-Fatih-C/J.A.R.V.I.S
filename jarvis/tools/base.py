"""Tool altyapısı — soyut Tool sınıfı, kayıt defteri ve LangChain adaptörü."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Tool(ABC):
    """Jarvis aracı için ortak arayüz.

    Alt sınıflar şu sınıf değişkenlerini tanımlar:
        name: Aracın benzersiz adı (modelin çağırdığı ad).
        description: Modelin aracı ne zaman kullanacağını anlatan açıklama.
        args_schema: Parametreleri tanımlayan Pydantic modeli.

    ve :meth:`run` metodunu uygular.
    """

    name: ClassVar[str]
    description: ClassVar[str]
    args_schema: ClassVar[type[BaseModel]]

    @abstractmethod
    async def run(self, **kwargs: Any) -> str:
        """Aracı verilen argümanlarla çalıştırır.

        Args:
            **kwargs: ``args_schema`` ile doğrulanmış parametreler.

        Returns:
            Modele geri verilecek metin sonucu.
        """
        raise NotImplementedError

    def to_langchain(self) -> StructuredTool:
        """Aracı LangChain :class:`StructuredTool`'a dönüştürür (agent için)."""

        async def _coro(**kwargs: Any) -> str:
            logger.info("Araç çağrıldı: %s(%s)", self.name, kwargs)
            return await self.run(**kwargs)

        return StructuredTool.from_function(
            coroutine=_coro,
            name=self.name,
            description=self.description,
            args_schema=self.args_schema,
        )


class ToolRegistry:
    """Araçları ada göre tutan ve LangChain'e açan kayıt defteri."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Bir aracı kaydeder (aynı ad varsa üzerine yazar).

        Args:
            tool: Kaydedilecek araç.
        """
        self._tools[tool.name] = tool
        logger.debug("Araç kaydedildi: %s", tool.name)

    def get(self, name: str) -> Tool:
        """Ada göre aracı döndürür.

        Args:
            name: Araç adı.

        Returns:
            Kayıtlı araç.

        Raises:
            KeyError: Araç kayıtlı değilse.
        """
        return self._tools[name]

    def all(self) -> list[Tool]:
        """Kayıtlı tüm araçları döndürür."""
        return list(self._tools.values())

    def names(self) -> list[str]:
        """Kayıtlı araç adlarını döndürür."""
        return list(self._tools.keys())

    def to_langchain(self) -> list[StructuredTool]:
        """Tüm araçları LangChain araç listesine dönüştürür."""
        return [tool.to_langchain() for tool in self._tools.values()]
