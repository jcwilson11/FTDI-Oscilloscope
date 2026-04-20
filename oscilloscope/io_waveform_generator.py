from __future__ import annotations

from .io_control_state import ioControlState
from .io_ftdi_waveform_source import ioFtdiWaveformSource
from .io_file_waveform_source import ioFileWaveformSource
from .io_generated_waveform_source import ioGeneratedWaveformSource
from .io_signal_source import ioSignalSource


class ioWaveformGenerator:
    """Generates deterministic sample streams for the oscilloscope demo."""

    def __init__(self, sources: list[ioSignalSource] | None = None):
        self.sources = list(
            sources
            or [
                ioFileWaveformSource(),
                ioFtdiWaveformSource(),
                ioGeneratedWaveformSource(),
            ]
        )

    def generate(self, control_state: ioControlState) -> list[float]:
        for source in self.sources:
            if source.supports(control_state.input_source):
                return source.generate(control_state)
        raise ValueError(f"Unsupported input source: {control_state.input_source}")
