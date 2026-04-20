from __future__ import annotations

from .data_buffer import ioDataBuffer
from .io_abstract_threaded_stream_worker import ioAbstractThreadedStreamWorker
from .io_output_scheduler import ioOutputScheduler
from .io_recovery_manager import ioRecoveryManager
from .io_throughput_monitor import ioThroughputMonitor
from .io_transfer_config import ioTransferConfig
from .io_writable_byte_stream import ioWritableByteStream


class ioUsbWriteController(ioAbstractThreadedStreamWorker):
    def __init__(
        self,
        stream: ioWritableByteStream,
        cfg: ioTransferConfig,
        buffer: ioDataBuffer,
        throughput_monitor: ioThroughputMonitor,
        recovery_manager: ioRecoveryManager,
        scheduler: ioOutputScheduler,
    ):
        super().__init__()
        self.stream = stream
        self.cfg = cfg
        self.buffer = buffer
        self.throughput_monitor = throughput_monitor
        self.recovery_manager = recovery_manager
        self.scheduler = scheduler

    def _run_worker(self) -> None:
        self.write_loop()

    def _handle_stop_without_thread(self) -> None:
        if self.stream.is_connected():
            self.stream.close()

    def _should_exit(self) -> bool:
        return not self.is_running() and self.buffer.is_empty()

    def _write_fully(self, data: bytes) -> None:
        offset = 0
        while offset < len(data):
            written = self.stream.write_bytes(data[offset:])
            if written <= 0:
                raise RuntimeError("Output stream made no forward progress during write.")
            if written > len(data) - offset:
                raise RuntimeError("Output stream reported writing more bytes than requested.")

            offset += written
            self.throughput_monitor.record_write(written)

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

                self._write_fully(data)
                self.scheduler.sleep_until_next_output(self.cfg.output_hz)

        except Exception as exc:
            self.recovery_manager.notify_user(f"Write failure: {exc}")
            self.recovery_manager.transition_to_safe_stop()
            self.buffer.close()


UsbWriteController = ioUsbWriteController
