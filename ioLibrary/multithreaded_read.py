from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

from ._ftdi_session import FtdiSession
from .data_buffer import DataBuffer
from .multithreaded_write import RecoveryManager


@dataclass
class AcquisitionConfig:
    input_hz: float = 10.0
    bytes_per_read: int = 8


class AcquisitionMonitor:
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


class InputScheduler:
    def __init__(self):
        self.next_time = None

    def sleep_until_next_input(self, input_hz: float) -> None:
        if input_hz <= 0:
            return

        period = 1.0 / input_hz
        now = time.perf_counter()

        if self.next_time is None:
            self.next_time = now + period
            return

        delay = self.next_time - now
        if delay > 0:
            time.sleep(delay)

        self.next_time += period


class FtdiByteStream:
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

    def read_bytes(self, count: int) -> bytes:
        if not self.connected or self.session is None:
            raise RuntimeError("Input stream is not open.")
        return self.session.read_bytes(count)

    def is_connected(self) -> bool:
        return self.connected


class UsbReadController:
    def __init__(
        self,
        stream: FtdiByteStream,
        cfg: AcquisitionConfig,
        buffer: DataBuffer,
        acquisition_monitor: AcquisitionMonitor,
        recovery_manager: RecoveryManager,
        scheduler: InputScheduler,
    ):
        self.stream = stream
        self.cfg = cfg
        self.buffer = buffer
        self.acquisition_monitor = acquisition_monitor
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

        self.thread = threading.Thread(target=self.read_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        with self.lock:
            self.running = False

        if self.thread is not None:
            self.thread.join(timeout=2.0)

        self.stream.close()

    def join(self, timeout: Optional[float] = None) -> None:
        if self.thread is not None:
            self.thread.join(timeout=timeout)

    def is_running(self) -> bool:
        with self.lock:
            return self.running

    def read_loop(self) -> None:
        try:
            while self.is_running():
                if not self.stream.is_connected():
                    self.recovery_manager.notify_user("Input connection lost.")
                    self.recovery_manager.transition_to_safe_stop()
                    self.buffer.close()
                    break

                data = self.stream.read_bytes(self.cfg.bytes_per_read)
                if data:
                    self.buffer.push(data)
                    self.acquisition_monitor.record_read(len(data))

                self.scheduler.sleep_until_next_input(self.cfg.input_hz)

        except Exception as exc:
            self.recovery_manager.notify_user(f"Read failure: {exc}")
            self.recovery_manager.transition_to_safe_stop()
            self.buffer.close()
        finally:
            self.stream.close()
            with self.lock:
                self.running = False
