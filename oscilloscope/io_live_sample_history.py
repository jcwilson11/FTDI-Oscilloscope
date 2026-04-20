from __future__ import annotations

from collections import deque
import threading


class ioLiveSampleHistory:
    """Thread-safe rolling byte history used for live waveform rendering."""

    def __init__(self, max_samples: int = 4096):
        self._max_samples = max(32, int(max_samples))
        self._samples = deque(maxlen=self._max_samples)
        self._total_samples = 0
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._samples.clear()
            self._total_samples = 0

    def append_bytes(self, payload: bytes) -> None:
        if not payload:
            return

        normalized = [((byte / 255.0) * 2.0) - 1.0 for byte in payload]
        with self._lock:
            self._samples.extend(normalized)
            self._total_samples += len(normalized)

    def latest_samples(self, limit: int | None = None) -> list[float]:
        with self._lock:
            samples = list(self._samples)

        if limit is None or limit >= len(samples):
            return samples
        return samples[-limit:]

    def total_samples(self) -> int:
        with self._lock:
            return self._total_samples

    def size(self) -> int:
        with self._lock:
            return len(self._samples)
