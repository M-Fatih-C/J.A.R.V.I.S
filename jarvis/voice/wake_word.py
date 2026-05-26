"""Wake word tespiti — openWakeWord ile "Hey Jarvis".

openWakeWord, hazır ``hey_jarvis`` modelini içerir. Model ilk kullanımda
lazy yüklenir (gerekirse indirilir). Test için dışarıdan bir model enjekte
edilebilir.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "hey_jarvis"
DEFAULT_THRESHOLD = 0.5
# openWakeWord 16 kHz, 80 ms (1280 örnek) int16 çerçevelerle çalışır.
FRAME_SAMPLES = 1280


class WakeWord:
    """openWakeWord tabanlı wake word detektörü.

    Attributes:
        model_name: Kullanılacak wake word modeli (ör. ``hey_jarvis``).
        threshold: Tetikleme eşiği (0-1).
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        threshold: float = DEFAULT_THRESHOLD,
        model: Any = None,
    ) -> None:
        """WakeWord'ü başlatır.

        Args:
            model_name: openWakeWord model adı.
            threshold: Tetikleme eşiği.
            model: Önceden hazır model (test/DI); ``None`` ise lazy yüklenir.
        """
        self.model_name = model_name
        self.threshold = threshold
        self._model = model

    def _ensure_loaded(self) -> None:
        """Model yüklü değilse (gerekirse indirip) yükler."""
        if self._model is not None:
            return
        import openwakeword
        from openwakeword.model import Model

        openwakeword.utils.download_models([self.model_name])
        logger.info("Wake word modeli yükleniyor: %s", self.model_name)
        self._model = Model(wakeword_models=[self.model_name])

    def predict(self, frame: np.ndarray) -> float:
        """Bir ses çerçevesi için wake word skorunu döndürür.

        Args:
            frame: 16 kHz int16 ses çerçevesi (genellikle 1280 örnek).

        Returns:
            ``model_name`` için 0-1 arası güven skoru.
        """
        self._ensure_loaded()
        scores = self._model.predict(frame)
        return float(scores.get(self.model_name, 0.0))

    def detected(self, frame: np.ndarray) -> bool:
        """Çerçevede wake word'ün tetiklenip tetiklenmediğini döndürür.

        Args:
            frame: 16 kHz int16 ses çerçevesi.

        Returns:
            Skor eşiği aşarsa ``True``.
        """
        return self.predict(frame) >= self.threshold

    def reset(self) -> None:
        """Detektörün iç durumunu sıfırlar (tetikleme sonrası önerilir)."""
        if self._model is not None and hasattr(self._model, "reset"):
            self._model.reset()
