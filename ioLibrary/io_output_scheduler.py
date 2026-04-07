import time


class ioOutputScheduler:
    def __init__(self):
        self.next_time = None

    def sleep_until_next_output(self, output_hz: float) -> None:
        if output_hz <= 0:
            return

        period = 1.0 / output_hz
        now = time.perf_counter()

        if self.next_time is None:
            self.next_time = now + period
            return

        delay = self.next_time - now
        if delay > 0:
            time.sleep(delay)

        self.next_time += period


OutputScheduler = ioOutputScheduler
