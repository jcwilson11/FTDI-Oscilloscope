from .io_rate_scheduler_base import ioRateSchedulerBase


class ioOutputScheduler(ioRateSchedulerBase):
    def sleep_until_next_output(self, output_hz: float) -> None:
        self._sleep_until_next_rate(output_hz)


OutputScheduler = ioOutputScheduler
