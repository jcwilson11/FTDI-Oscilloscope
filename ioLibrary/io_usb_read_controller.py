from __future__ import annotations

from .data_buffer import ioDataBuffer
from .io_acquisition_config import ioAcquisitionConfig
from .io_acquisition_monitor import ioAcquisitionMonitor
from .io_abstract_threaded_stream_worker import ioAbstractThreadedStreamWorker
from .io_input_scheduler import ioInputScheduler
from .io_readable_byte_stream import ioReadableByteStream
from .io_recovery_manager import ioRecoveryManager


class ioUsbReadController(ioAbstractThreadedStreamWorker):
    def __init__(
        self,
        stream: ioReadableByteStream,
        cfg: ioAcquisitionConfig,
        buffer: ioDataBuffer,
        acquisition_monitor: ioAcquisitionMonitor,
        recovery_manager: ioRecoveryManager,
        scheduler: ioInputScheduler,
    ):
        super().__init__()
        self.stream = stream
        self.cfg = cfg
        self.buffer = buffer
        self.acquisition_monitor = acquisition_monitor
        self.recovery_manager = recovery_manager
        self.scheduler = scheduler

    def _run_worker(self) -> None:
        self.read_loop()

    def _after_stop_joined(self) -> None:
        self.stream.close()

    def _handle_stop_without_thread(self) -> None:
        self.stream.close()

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


UsbReadController = ioUsbReadController
