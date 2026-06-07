from collections import Counter
from threading import Lock
from typing import Any


class MetricsCollector:
    """In-process metrics sink used locally and in tests.

    Production deployments can bridge these counters to Prometheus or OTLP without
    changing the runtime call sites.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self.counters: Counter[str] = Counter()
        self.timings: dict[str, list[float]] = {}

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self.counters[name] += amount

    def observe_ms(self, name: str, value: float) -> None:
        with self._lock:
            self.timings.setdefault(name, []).append(value)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {"counters": dict(self.counters), "timings": {k: list(v) for k, v in self.timings.items()}}

