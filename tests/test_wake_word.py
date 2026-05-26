"""WakeWord testleri — model enjekte edilerek (openWakeWord indirmesi olmadan)."""

from __future__ import annotations

import numpy as np

from jarvis.voice.wake_word import WakeWord


class FakeModel:
    """Sabit skor döndüren sahte openWakeWord modeli."""

    def __init__(self, score: float) -> None:
        self.score = score
        self.reset_called = False

    def predict(self, frame: np.ndarray) -> dict[str, float]:
        return {"hey_jarvis": self.score}

    def reset(self) -> None:
        self.reset_called = True


_FRAME = np.zeros(1280, dtype=np.int16)


def test_predict_returns_score() -> None:
    ww = WakeWord(model=FakeModel(0.83))
    assert ww.predict(_FRAME) == 0.83


def test_detected_above_threshold() -> None:
    ww = WakeWord(threshold=0.5, model=FakeModel(0.9))
    assert ww.detected(_FRAME) is True


def test_not_detected_below_threshold() -> None:
    ww = WakeWord(threshold=0.5, model=FakeModel(0.2))
    assert ww.detected(_FRAME) is False


def test_threshold_boundary() -> None:
    ww = WakeWord(threshold=0.5, model=FakeModel(0.5))
    assert ww.detected(_FRAME) is True  # >= eşik


def test_reset_delegates_to_model() -> None:
    fake = FakeModel(0.0)
    ww = WakeWord(model=fake)
    ww.reset()
    assert fake.reset_called is True
