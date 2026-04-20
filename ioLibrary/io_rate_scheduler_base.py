from __future__ import annotations

import time
from abc import ABC


class ioRateSchedulerBase(ABC):
    def __init__(self):
        self.next_time = None

    def _sleep_until_next_rate(self, rate_hz: float) -> None:
        if rate_hz <= 0:
            return

        period = 1.0 / rate_hz
        now = time.perf_counter()

        if self.next_time is None:
            self.next_time = now + period
            return

        delay = self.next_time - now
        if delay > 0:
            time.sleep(delay)

        self.next_time += period


RateSchedulerBase = ioRateSchedulerBase
