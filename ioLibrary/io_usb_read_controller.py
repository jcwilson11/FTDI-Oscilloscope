from __future__ import annotations

import threading
from typing import Optional

from .data_buffer import ioDataBuffer
from .io_acquisition_config import ioAcquisitionConfig
from .io_acquisition_monitor import ioAcquisitionMonitor
from .io_input_scheduler import ioInputScheduler
from .io_readable_byte_stream import ioReadableByteStream
from .io_recovery_manager import ioRecoveryManager


class ioUsbReadController:
    def __init__(
        self,
        stream: ioReadableByteStream,
        cfg: ioAcquisitionConfig,
        buffer: ioDataBuffer,
        acquisition_monitor: ioAcquisitionMonitor,
        recovery_manager: ioRecoveryManager,
        scheduler: ioInputScheduler,
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
                elif self.stream.is_exhausted():
                    self.buffer.close()
                    break

                self.scheduler.sleep_until_next_input(self.cfg.input_hz)

        except Exception as exc:
            self.recovery_manager.notify_user(f"Read failure: {exc}")
            self.recovery_manager.transition_to_safe_stop()
            self.buffer.close()
        finally:
            self.stream.close()
            with self.lock:
                self.running = False


UsbReadController = ioUsbReadController
