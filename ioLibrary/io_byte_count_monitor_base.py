from __future__ import annotations

import threading
import time
from abc import ABC


class ioByteCountMonitorBase(ABC):
    def __init__(self):
        self._total_count = 0
        self.start_time = time.perf_counter()
        self.lock = threading.Lock()

    def _record_bytes(self, nbytes: int) -> None:
        with self.lock:
            self._total_count += nbytes

    def _get_total_count(self) -> int:
        with self.lock:
            return self._total_count

    def throughput_kbps(self) -> float:
        with self.lock:
            elapsed = time.perf_counter() - self.start_time
            if elapsed <= 0:
                return 0.0
            return (self._total_count / 1024.0) / elapsed


ByteCountMonitorBase = ioByteCountMonitorBase
