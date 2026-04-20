from __future__ import annotations

import threading
from typing import Optional

from .data_buffer import ioDataBuffer
from .io_acquisition_config import ioAcquisitionConfig
from .io_acquisition_monitor import ioAcquisitionMonitor
from .io_file_input_byte_stream import ioFileInputByteStream
from .io_file_byte_stream import ioFileByteStream
from .io_ftdi_byte_stream import ioFtdiByteStream
from .io_ftdi_output_byte_stream import ioFtdiOutputByteStream
from .io_input_scheduler import ioInputScheduler
from .io_output_scheduler import ioOutputScheduler
from .io_pipeline_config import ioPipelineConfig
from .io_readable_byte_stream import ioReadableByteStream
from .io_recovery_manager import ioRecoveryManager
from .io_throughput_monitor import ioThroughputMonitor
from .io_transfer_config import ioTransferConfig
from .io_usb_read_controller import ioUsbReadController
from .io_usb_write_controller import ioUsbWriteController
from .io_writable_byte_stream import ioWritableByteStream


class ioPipelineController:
    def __init__(
        self,
        cfg: ioPipelineConfig,
        *,
        input_stream: Optional[ioReadableByteStream] = None,
        output_stream: Optional[ioWritableByteStream] = None,
    ):
        self.cfg = cfg
        self.buffer = ioDataBuffer(capacity=cfg.buffer_capacity)
        self.recovery_manager = ioRecoveryManager()
        self.acquisition_monitor = ioAcquisitionMonitor()
        self.throughput_monitor = ioThroughputMonitor()
        self.input_scheduler = ioInputScheduler()
        self.output_scheduler = ioOutputScheduler()

        self.input_stream = input_stream or self._build_input_stream()
        self.output_stream = output_stream or self._build_output_stream()

        self.reader = ioUsbReadController(
            stream=self.input_stream,
            cfg=ioAcquisitionConfig(
                input_hz=cfg.input_hz,
                bytes_per_read=cfg.bytes_per_read,
            ),
            buffer=self.buffer,
            acquisition_monitor=self.acquisition_monitor,
            recovery_manager=self.recovery_manager,
            scheduler=self.input_scheduler,
        )
        self.writer = ioUsbWriteController(
            stream=self.output_stream,
            cfg=ioTransferConfig(
                output_hz=cfg.output_hz,
                bytes_per_write=cfg.bytes_per_write,
            ),
            buffer=self.buffer,
            throughput_monitor=self.throughput_monitor,
            recovery_manager=self.recovery_manager,
            scheduler=self.output_scheduler,
        )

        self._started = False
        self._lock = threading.Lock()

    def _build_input_stream(self):
        if self.cfg.input_mode == "file":
            return ioFileInputByteStream(self.cfg.input_path)
        return ioFtdiByteStream(
            device_index=self.cfg.input_device_index,
            dll_path=self.cfg.dll_path,
        )

    def _build_output_stream(self):
        if self.cfg.output_mode == "file":
            return ioFileByteStream(
                self.cfg.output_path,
                append=self.cfg.append_output,
            )
        return ioFtdiOutputByteStream(
            device_index=self.cfg.output_device_index or 0,
            dll_path=self.cfg.dll_path,
        )

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True

        self.writer.start()
        self.reader.start()

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            self._started = False

        self.reader.stop()
        self.buffer.close()
        self.writer.stop()

    def join(self, timeout: float | None = None) -> None:
        if timeout is None:
            self.reader.join()
            self.writer.join()
            return

        split_timeout = timeout / 2.0
        self.reader.join(split_timeout)
        self.writer.join(split_timeout)

    def is_running(self) -> bool:
        return self.reader.is_running() or self.writer.is_running()

    def status_snapshot(self) -> dict:
        return {
            "input_mode": self.cfg.input_mode,
            "output_mode": self.cfg.output_mode,
            "bytes_read": self.acquisition_monitor.total_read,
            "bytes_written": self.throughput_monitor.total_written,
            "read_throughput_kbps": self.acquisition_monitor.throughput_kbps(),
            "write_throughput_kbps": self.throughput_monitor.throughput_kbps(),
            "buffer_size": self.buffer.size(),
            "buffer_capacity": self.buffer.capacity,
            "buffer_closed": self.buffer.is_closed(),
            "reader_running": self.reader.is_running(),
            "writer_running": self.writer.is_running(),
            "safe_stopped": self.recovery_manager.safe_stopped,
            "recovery_messages": list(self.recovery_manager.messages),
        }


PipelineController = ioPipelineController
