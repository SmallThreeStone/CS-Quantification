from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock


@dataclass
class ApiLatencySample:
    path: str
    method: str
    status_code: int
    duration_ms: float
    created_at: datetime


class ApiMetricsStore:
    def __init__(self, max_samples: int = 2000) -> None:
        self._samples: deque[ApiLatencySample] = deque(maxlen=max_samples)
        self._lock = Lock()

    def record(self, path: str, method: str, status_code: int, duration_ms: float) -> None:
        sample = ApiLatencySample(
            path=path,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            created_at=datetime.utcnow(),
        )
        with self._lock:
            self._samples.append(sample)

    def recent(self, window_minutes: int) -> list[ApiLatencySample]:
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        with self._lock:
            return [sample for sample in self._samples if sample.created_at >= cutoff]

    def clear(self) -> None:
        with self._lock:
            self._samples.clear()


api_metrics_store = ApiMetricsStore()
