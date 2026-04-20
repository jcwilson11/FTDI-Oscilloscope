from .io_rate_scheduler_base import ioRateSchedulerBase


class ioInputScheduler(ioRateSchedulerBase):
    def sleep_until_next_input(self, input_hz: float) -> None:
        self._sleep_until_next_rate(input_hz)


InputScheduler = ioInputScheduler
