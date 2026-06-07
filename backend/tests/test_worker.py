import pytest

from app.config import settings
from app.jobs import worker


def test_worker_main_uses_configured_sleep(monkeypatch):
    previous_sleep = settings.worker_sleep_seconds
    settings.worker_sleep_seconds = 7
    sleeps: list[int] = []
    monkeypatch.setattr(worker, "run_once", lambda: 0)

    def fake_sleep(seconds: int):
        sleeps.append(seconds)
        raise KeyboardInterrupt

    monkeypatch.setattr(worker.time, "sleep", fake_sleep)
    try:
        with pytest.raises(KeyboardInterrupt):
            worker.main()
    finally:
        settings.worker_sleep_seconds = previous_sleep

    assert sleeps == [7]
