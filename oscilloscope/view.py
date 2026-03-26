from __future__ import annotations


class OscilloscopeView:
    """View boundary that renders processed signal data only."""

    def __init__(self, canvas: str = "Canvas", controls: str = "ControlPanel"):
        self.canvas = canvas
        self.controls = controls
        self.lastRenderedSignal: list[float] = []

    def render(self, signal: list[float]) -> dict:
        self.lastRenderedSignal = list(signal)
        return {
            "canvas": self.canvas,
            "controls": self.controls,
            "signal": list(signal),
        }

    def getUserInput(self, command: str) -> str:
        return command
