from __future__ import annotations

from typing import Callable

from ioLibrary import ioFtdiByteStream

from .io_control_state import ioControlState


class ioFtdiWaveformSource:
    """Acquire waveform samples from an FTDI device through the IO library."""

    def __init__(self, stream_factory: Callable[..., ioFtdiByteStream] | None = None):
        self._stream_factory = stream_factory if stream_factory is not None else ioFtdiByteStream

    def supports(self, input_source: str) -> bool:
        return input_source.startswith("ftdi")

    def generate(self, control_state: ioControlState) -> list[float]:
        sample_count = max(
            1,
            int(round(control_state.sample_duration_seconds / control_state.sample_time_seconds)),
        )
        device_index = self._resolve_device_index(control_state)
        stream = self._stream_factory(
            device_index=device_index,
            dll_path=control_state.ftdi_dll_path or None,
        )
        stream.open()
        try:
            payload = stream.read_bytes(sample_count)
        finally:
            stream.close()

        if not payload:
            return [0.0]
        return [((byte / 255.0) * 2.0) - 1.0 for byte in payload]

    def _resolve_device_index(self, control_state: ioControlState) -> int:
        if ":" not in control_state.input_source:
            return control_state.ftdi_input_device_index

        _, raw_index = control_state.input_source.split(":", 1)
        raw_index = raw_index.strip()
        if not raw_index:
            return control_state.ftdi_input_device_index
        return int(raw_index)
