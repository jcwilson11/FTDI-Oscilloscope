from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional, Protocol

from ._ftdi_session import FtdiSession


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


class WritableByteStream(Protocol):
    def open(self) -> None:
        ...

    def close(self) -> None:
        ...

    def write_bytes(self, data: bytes) -> int:
        ...

    def is_connected(self) -> bool:
        ...


class DataBuffer:
    def __init__(self, capacity: int = 1024):
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")

        self.capacity = capacity
        self._storage = bytearray(capacity)
        self._head = 0
        self._tail = 0
        self._count = 0
        self._closed = False
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

    def push(self, data: bytes) -> None:
        if not data:
            return

        payload = memoryview(bytes(data))
        offset = 0
        with self._lock:
            while offset < len(payload):
                while self._count >= self.capacity and not self._closed:
                    self._not_full.wait()

                if self._closed:
                    raise RuntimeError("Cannot push to closed buffer.")

                writable = min(self.capacity - self._count, len(payload) - offset)
                first = min(writable, self.capacity - self._tail)
                self._storage[self._tail : self._tail + first] = payload[offset : offset + first]
                self._tail = (self._tail + first) % self.capacity
                offset += first
                self._count += first

                second = writable - first
                if second:
                    self._storage[self._tail : self._tail + second] = payload[offset : offset + second]
                    self._tail = (self._tail + second) % self.capacity
                    offset += second
                    self._count += second

                self._not_empty.notify_all()

    def pop(self, n: int, timeout: Optional[float] = None) -> bytes:
        if n <= 0:
            return b""

        with self._lock:
            if timeout is None:
                while self._count == 0 and not self._closed:
                    self._not_empty.wait()
            else:
                end_time = time.perf_counter() + timeout
                while self._count == 0 and not self._closed:
                    remaining = end_time - time.perf_counter()
                    if remaining <= 0:
                        return b""
                    self._not_empty.wait(timeout=remaining)

            if self._count == 0 and self._closed:
                return b""

            readable = min(n, self._count)
            out = bytearray(readable)
            first = min(readable, self.capacity - self._head)
            out[:first] = self._storage[self._head : self._head + first]
            self._head = (self._head + first) % self.capacity
            self._count -= first

            second = readable - first
            if second:
                out[first:] = self._storage[self._head : self._head + second]
                self._head = (self._head + second) % self.capacity
                self._count -= second

            self._not_full.notify_all()
            return bytes(out)

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._not_empty.notify_all()
            self._not_full.notify_all()

    def is_closed(self) -> bool:
        with self._lock:
            return self._closed

    def is_empty(self) -> bool:
        with self._lock:
            return self._count == 0

    def is_full(self) -> bool:
        with self._lock:
            return self._count == self.capacity

    def size(self) -> int:
        with self._lock:
            return self._count

    def available_space(self) -> int:
        with self._lock:
            return self.capacity - self._count


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


class FtdiOutputByteStream:
    def __init__(
        self,
        *,
        device_index: int = 0,
        dll_path: str | None = None,
        session_factory: Optional[Callable[[], object]] = None,
    ):
        self.device_index = device_index
        self.dll_path = dll_path
        self.session_factory = session_factory or (
            lambda: FtdiSession(dll_path=self.dll_path, device_index=self.device_index)
        )
        self.session = None
        self.connected = False

    def open(self) -> None:
        session = self.session_factory()
        if hasattr(session, "__enter__"):
            session = session.__enter__()
        else:
            session.open()
            if hasattr(session, "initialize_bitbang"):
                session.initialize_bitbang()
        self.session = session
        self.connected = True

    def close(self) -> None:
        if self.session is None:
            self.connected = False
            return

        try:
            if hasattr(self.session, "__exit__"):
                self.session.__exit__(None, None, None)
            else:
                self.session.close()
        finally:
            self.session = None
            self.connected = False

    def write_bytes(self, data: bytes) -> int:
        if not self.connected or self.session is None:
            raise RuntimeError("Output stream is not open.")
        return self.session.write_bytes(data)

    def is_connected(self) -> bool:
        return self.connected


class UsbWriteController:
    def __init__(
        self,
        stream: WritableByteStream,
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

        if self.thread is not None:
            self.thread.join(timeout=2.0)

        if self.stream.is_connected():
            self.stream.close()

    def join(self, timeout: Optional[float] = None) -> None:
        if self.thread is not None:
            self.thread.join(timeout=timeout)

    def is_running(self) -> bool:
        with self.lock:
            return self.running

    def _should_exit(self) -> bool:
        return not self.is_running() and self.buffer.is_empty()

    def write_loop(self) -> None:
        try:
            while True:
                if self._should_exit():
                    break

                if not self.stream.is_connected():
                    self.recovery_manager.notify_user("Output connection lost.")
                    self.recovery_manager.transition_to_safe_stop()
                    self.buffer.close()
                    break

                data = self.buffer.pop(self.cfg.bytes_per_write, timeout=0.5)
                if not data:
                    if self._should_exit() or (self.buffer.is_closed() and self.buffer.is_empty()):
                        break
                    continue

                written = self.stream.write_bytes(data)
                self.throughput_monitor.record_write(written)
                self.scheduler.sleep_until_next_output(self.cfg.output_hz)

        except Exception as exc:
            self.recovery_manager.notify_user(f"Write failure: {exc}")
            self.recovery_manager.transition_to_safe_stop()
            self.buffer.close()
        finally:
            with self.lock:
                self.running = False
