from __future__ import annotations

from pathlib import Path

from .io_control_state import ioControlState


class ioFileWaveformSource:
    def supports(self, input_source: str) -> bool:
        return input_source.startswith("file:")

    def generate(self, control_state: ioControlState) -> list[float]:
        path = Path(control_state.input_source[5:])
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")

        payload = path.read_bytes()
        if not payload:
            return [0.0]
        return [((byte / 255.0) * 2.0) - 1.0 for byte in payload]


FileWaveformSource = ioFileWaveformSource
