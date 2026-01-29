# tests/conftest.py
import sys
from pathlib import Path
import pytest

from tests.fakes.fake_clock import FakeClock


class _FakeTime:
    """只給 module-under-test 用的 time，不要動到 stdlib time module。"""
    def __init__(self, clock: FakeClock):
        self._clock = clock

    def time(self) -> float:
        return self._clock.time()

    def sleep(self, seconds: float) -> None:
        self._clock.sleep(seconds)


@pytest.fixture
def fake_clock():
    return FakeClock(start=0)


@pytest.fixture
def m():
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    import scripts.hedge_bp_aster_futures_loop as module
    return module


@pytest.fixture
def patch_time(monkeypatch, m, fake_clock):
    # 只替換模組內的 time 變數，避免影響 Allure/pytest 自己的計時
    monkeypatch.setattr(m, "time", _FakeTime(fake_clock), raising=True)
    return m