from __future__ import annotations

import math


class ioGeneratedWaveformByteStream:
    """Continuous generated waveform source exposed as a readable byte stream."""

    def __init__(self, waveform: str = "sine", samples_per_cycle: int = 200):
        self.waveform = waveform
        self.samples_per_cycle = max(16, int(samples_per_cycle))
        self.connected = False
        self._sample_index = 0

    def open(self) -> None:
        self.connected = True
        self._sample_index = 0

    def close(self) -> None:
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def is_exhausted(self) -> bool:
        return False

    def read_bytes(self, count: int) -> bytes:
        if not self.connected:
            raise RuntimeError("Input stream is not open.")

        payload = bytearray()
        for _ in range(max(0, count)):
            sample = self._sample_value(self._sample_index)
            payload.append(self._to_byte(sample))
            self._sample_index += 1
        return bytes(payload)

    def _sample_value(self, index: int) -> float:
        phase = (index % self.samples_per_cycle) / self.samples_per_cycle
        radians = phase * 2.0 * math.pi

        if self.waveform == "sine":
            return math.sin(radians)
        if self.waveform == "square":
            return 1.0 if math.sin(radians) >= 0.0 else -1.0
        if self.waveform == "triangle":
            return 1.0 - (4.0 * abs(phase - 0.5))
        if self.waveform == "sawtooth":
            return (phase * 2.0) - 1.0
        return math.sin(radians)

    def _to_byte(self, sample: float) -> int:
        normalized = max(-1.0, min(1.0, sample))
        return int(round(((normalized + 1.0) / 2.0) * 255.0))
