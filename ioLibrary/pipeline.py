from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional

from .data_buffer import DataBuffer
from .multithreaded_read import (
    AcquisitionConfig,
    AcquisitionMonitor,
    FtdiByteStream,
    InputScheduler,
    UsbReadController,
)
from .multithreaded_write import (
    FileByteStream,
    FtdiOutputByteStream,
    OutputScheduler,
    RecoveryManager,
    ThroughputMonitor,
    TransferConfig,
    UsbWriteController,
)


@dataclass
class PipelineConfig:
    input_device_index: int = 0
    output_mode: str = "file"
    output_path: str | None = None
    output_device_index: int | None = None
    bytes_per_read: int = 8
    bytes_per_write: int = 8
    input_hz: float = 10.0
    output_hz: float = 10.0
    buffer_capacity: int = 1024
    dll_path: str | None = None

    def __post_init__(self) -> None:
        if self.output_mode not in {"file", "ftdi"}:
            raise ValueError("output_mode must be 'file' or 'ftdi'")
        if self.output_mode == "file" and not self.output_path:
            raise ValueError("file output mode requires output_path")
        if self.output_mode == "ftdi" and self.output_device_index is None:
            raise ValueError("ftdi output mode requires output_device_index")
        if self.bytes_per_read <= 0 or self.bytes_per_write <= 0:
            raise ValueError("chunk sizes must be greater than zero")
        if self.input_hz <= 0 or self.output_hz <= 0:
            raise ValueError("input_hz and output_hz must be greater than zero")
        if self.buffer_capacity <= 0:
            raise ValueError("buffer_capacity must be greater than zero")
        if self.buffer_capacity < max(self.bytes_per_read, self.bytes_per_write):
            raise ValueError("buffer_capacity must be at least the largest chunk size")


class PipelineController:
    def __init__(
        self,
        cfg: PipelineConfig,
        *,
        input_stream: Optional[FtdiByteStream] = None,
        output_stream=None,
    ):
        self.cfg = cfg
        self.buffer = DataBuffer(capacity=cfg.buffer_capacity)
        self.recovery_manager = RecoveryManager()
        self.acquisition_monitor = AcquisitionMonitor()
        self.throughput_monitor = ThroughputMonitor()
        self.input_scheduler = InputScheduler()
        self.output_scheduler = OutputScheduler()

        self.input_stream = input_stream or FtdiByteStream(
            device_index=cfg.input_device_index,
            dll_path=cfg.dll_path,
        )
        self.output_stream = output_stream or self._build_output_stream()

        self.reader = UsbReadController(
            stream=self.input_stream,
            cfg=AcquisitionConfig(
                input_hz=cfg.input_hz,
                bytes_per_read=cfg.bytes_per_read,
            ),
            buffer=self.buffer,
            acquisition_monitor=self.acquisition_monitor,
            recovery_manager=self.recovery_manager,
            scheduler=self.input_scheduler,
        )
        self.writer = UsbWriteController(
            stream=self.output_stream,
            cfg=TransferConfig(
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

    def _build_output_stream(self):
        if self.cfg.output_mode == "file":
            return FileByteStream(self.cfg.output_path)
        return FtdiOutputByteStream(
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
