import threading
import time


class ioThroughputMonitor:
    def __init__(self):
        self.total_written = 0
        self.start_time = time.perf_counter()
        self.lock = threading.Lock()

    def record_write(self, nbytes: int) -> None:
        with self.lock:
            self.total_written += nbytes

    def throughput_kbps(self) -> float:
        with self.lock:
            elapsed = time.perf_counter() - self.start_time
            if elapsed <= 0:
                return 0.0
            return (self.total_written / 1024.0) / elapsed


ThroughputMonitor = ioThroughputMonitor
