import threading
import time
from dataclasses import dataclass
from collections import deque
from typing import Optional


@dataclass
class TransferConfig:
    output_hz: float = 10.0
    bytes_per_write: int = 8


class ThroughputMonitor:
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


class RecoveryManager:
    def __init__(self):
        self.messages = []
        self.safe_stopped = False

    def notify_user(self, msg: str) -> None:
        self.messages.append(msg)
        print(f"[RecoveryManager] {msg}")

    def transition_to_safe_stop(self) -> None:
        self.safe_stopped = True
        print("[RecoveryManager] Transitioning to safe stop.")


class OutputScheduler:
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


class DataBuffer:
    def __init__(self, capacity: int = 1024):
        self.capacity = capacity
        self.buffer = deque()
        self.size_count = 0
        self.closed = False
        self.condition = threading.Condition()

    def push(self, data: bytes) -> None:
        if not data:
            return

        with self.condition:
            for b in data:
                while self.size_count >= self.capacity and not self.closed:
                    self.condition.wait()

                if self.closed:
                    raise RuntimeError("Cannot push to closed buffer.")

                self.buffer.append(b)
                self.size_count += 1

            self.condition.notify_all()

    def pop(self, n: int, timeout: Optional[float] = None) -> bytes:
        with self.condition:
            if timeout is None:
                while self.size_count == 0 and not self.closed:
                    self.condition.wait()
            else:
                end_time = time.perf_counter() + timeout
                while self.size_count == 0 and not self.closed:
                    remaining = end_time - time.perf_counter()
                    if remaining <= 0:
                        return b""
                    self.condition.wait(timeout=remaining)

            if self.size_count == 0 and self.closed:
                return b""

            count = min(n, self.size_count)
            out = bytearray()

            for _ in range(count):
                out.append(self.buffer.popleft())
                self.size_count -= 1

            self.condition.notify_all()
            return bytes(out)

    def close(self) -> None:
        with self.condition:
            self.closed = True
            self.condition.notify_all()


class FileByteStream:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.file_handle = None
        self.connected = False

    def open(self) -> None:
        self.file_handle = open(self.output_path, "ab")
        self.connected = True

    def close(self) -> None:
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        self.connected = False

    def write_bytes(self, data: bytes) -> int:
        if not self.connected or self.file_handle is None:
            raise RuntimeError("Output stream is not open.")
        self.file_handle.write(data)
        self.file_handle.flush()
        return len(data)

    def is_connected(self) -> bool:
        return self.connected


class UsbWriteController:
    def __init__(
        self,
        stream: FileByteStream,
        cfg: TransferConfig,
        buffer: DataBuffer,
        throughput_monitor: ThroughputMonitor,
        recovery_manager: RecoveryManager,
        scheduler: OutputScheduler,
    ):
        self.stream = stream
        self.cfg = cfg
        self.buffer = buffer
        self.throughput_monitor = throughput_monitor
        self.recovery_manager = recovery_manager
        self.scheduler = scheduler
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self) -> None:
        with self.lock:
            if self.running:
                return
            self.running = True

        if not self.stream.is_connected():
            self.stream.open()

        self.thread = threading.Thread(target=self.write_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        with self.lock:
            self.running = False

        self.buffer.close()

        if self.thread is not None:
            self.thread.join(timeout=2.0)

        if self.stream.is_connected():
            self.stream.close()

    def is_running(self) -> bool:
        with self.lock:
            return self.running

    def write_loop(self) -> None:
        try:
            while self.is_running():
                if not self.stream.is_connected():
                    self.recovery_manager.notify_user("Output connection lost.")
                    self.recovery_manager.transition_to_safe_stop()
                    break

                data = self.buffer.pop(self.cfg.bytes_per_write, timeout=0.5)

                if not data:
                    continue

                written = self.stream.write_bytes(data)
                self.throughput_monitor.record_write(written)
                self.scheduler.sleep_until_next_output(self.cfg.output_hz)

        except Exception as exc:
            self.recovery_manager.notify_user(f"Write failure: {exc}")
            self.recovery_manager.transition_to_safe_stop()
        finally:
            with self.lock:
                self.running = False