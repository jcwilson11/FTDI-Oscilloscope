from __future__ import annotations

import math

from .io_control_state import ioControlState


class ioGeneratedWaveformSource:
    def supports(self, input_source: str) -> bool:
        return not input_source.startswith("file:")

    def generate(self, control_state: ioControlState) -> list[float]:
        sample_count = max(
            1,
            int(round(control_state.sample_duration_seconds / control_state.sample_time_seconds)),
        )
        waveform = control_state.input_source.lower()
        return [self._waveform_value(waveform, index, sample_count) for index in range(sample_count)]

    def _waveform_value(self, waveform: str, index: int, sample_count: int) -> float:
        phase = (index / max(sample_count, 1)) * 4.0
        radians = phase * 2.0 * math.pi

        if waveform == "sine":
            return math.sin(radians)
        if waveform == "square":
            return 1.0 if math.sin(radians) >= 0.0 else -1.0
        if waveform == "triangle":
            position = phase % 1.0
            return 1.0 - (4.0 * abs(position - 0.5))
        if waveform == "sawtooth":
            return ((phase % 1.0) * 2.0) - 1.0
        raise ValueError(f"Unsupported input source: {waveform}")


GeneratedWaveformSource = ioGeneratedWaveformSource
