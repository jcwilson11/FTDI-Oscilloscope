import threading
import time


class ioAcquisitionMonitor:
    def __init__(self):
        self.total_read = 0
        self.start_time = time.perf_counter()
        self.lock = threading.Lock()

    def record_read(self, nbytes: int) -> None:
        with self.lock:
            self.total_read += nbytes

    def throughput_kbps(self) -> float:
        with self.lock:
            elapsed = time.perf_counter() - self.start_time
            if elapsed <= 0:
                return 0.0
            return (self.total_read / 1024.0) / elapsed


AcquisitionMonitor = ioAcquisitionMonitor
