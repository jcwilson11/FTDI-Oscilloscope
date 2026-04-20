from __future__ import annotations

from ioLibrary import (
    ioFileByteStream,
    ioFtdiByteStream,
    ioFtdiOutputByteStream,
    ioPipelineConfig,
    ioPipelineController,
)

from .io_control_state import ioControlState
from .io_generated_waveform_byte_stream import ioGeneratedWaveformByteStream
from .io_live_file_tail_byte_stream import ioLiveFileTailByteStream
from .io_live_sample_history import ioLiveSampleHistory
from .io_null_writable_byte_stream import ioNullWritableByteStream
from .io_tapped_readable_byte_stream import ioTappedReadableByteStream


class ioLiveOscilloscopeSession:
    """Owns the live acquisition pipeline and rolling waveform history."""

    def __init__(self, history: ioLiveSampleHistory | None = None):
        self.history = history if history is not None else ioLiveSampleHistory()
        self.pipeline: ioPipelineController | None = None
        self._last_snapshot: dict[str, object] = {}

    def start(self, control_state: ioControlState, *, history_size: int = 4096) -> None:
        self.stop()
        self.history = ioLiveSampleHistory(max_samples=history_size)

        input_stream = ioTappedReadableByteStream(
            self._build_input_stream(control_state),
            self.history,
        )
        output_stream = self._build_output_stream(control_state)
        cfg = self._build_pipeline_config(control_state)
        self.pipeline = ioPipelineController(cfg, input_stream=input_stream, output_stream=output_stream)
        self.pipeline.start()
        self._last_snapshot = {}

    def stop(self) -> None:
        if self.pipeline is None:
            return
        self.pipeline.stop()
        self._last_snapshot = self.status_snapshot()
        self.pipeline = None

    def is_running(self) -> bool:
        return self.pipeline is not None and self.pipeline.is_running()

    def latest_samples(self, limit: int) -> list[float]:
        return self.history.latest_samples(limit)

    def status_snapshot(self) -> dict[str, object]:
        if self.pipeline is None:
            return {
                "running": False,
                "sample_history_size": self.history.size(),
                "total_samples": self.history.total_samples(),
                "bytes_read": 0,
                "bytes_written": 0,
                "buffer_size": 0,
                "safe_stopped": False,
                "recovery_messages": [],
                "tee_mode": "none",
            }

        snapshot = self.pipeline.status_snapshot()
        snapshot["running"] = self.pipeline.is_running()
        snapshot["sample_history_size"] = self.history.size()
        snapshot["total_samples"] = self.history.total_samples()
        return snapshot

    def _build_input_stream(self, control_state: ioControlState):
        if control_state.input_source.startswith("ftdi"):
            return ioFtdiByteStream(
                device_index=control_state.ftdi_input_device_index,
                dll_path=control_state.ftdi_dll_path or None,
            )
        if control_state.input_source.startswith("file:"):
            return ioLiveFileTailByteStream(control_state.live_file_path)
        return ioGeneratedWaveformByteStream(control_state.generated_waveform)

    def _build_output_stream(self, control_state: ioControlState):
        if not control_state.tee_output_enabled or control_state.tee_output_mode == "none":
            return ioNullWritableByteStream()
        if control_state.tee_output_mode == "ftdi":
            return ioFtdiOutputByteStream(
                device_index=control_state.ftdi_output_device_index,
                dll_path=control_state.ftdi_dll_path or None,
            )
        return ioFileByteStream(control_state.tee_output_path, append=False)

    def _build_pipeline_config(self, control_state: ioControlState) -> ioPipelineConfig:
        chunk_size = max(1, min(control_state.ftdi_bytes_per_read, 64))
        loop_hz = 1.0 / max(control_state.sample_time_seconds * chunk_size, 0.01)
        loop_hz = max(5.0, min(200.0, loop_hz))
        buffer_capacity = max(1024, chunk_size * 4)

        input_mode = "ftdi" if control_state.input_source.startswith("ftdi") else "file"
        output_mode = "ftdi" if control_state.tee_output_mode == "ftdi" else "file"

        return ioPipelineConfig(
            input_mode=input_mode,
            input_device_index=control_state.ftdi_input_device_index,
            input_path=control_state.live_file_path,
            output_mode=output_mode,
            output_path=control_state.tee_output_path or "live_scope_capture.bin",
            output_device_index=control_state.ftdi_output_device_index,
            append_output=False,
            bytes_per_read=chunk_size,
            bytes_per_write=chunk_size,
            input_hz=loop_hz,
            output_hz=loop_hz,
            buffer_capacity=buffer_capacity,
            dll_path=control_state.ftdi_dll_path or None,
        )
