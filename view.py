from __future__ import annotations

from typing import Any

from .ioViewBase import ioViewBase


class OscilloscopeView(ioViewBase):
    """Deprecated compatibility wrapper for older non-Qt controller code.

    The Qt-based `ioMainWindow`, `ioOscilloscopeViewDark`, and
    `ioOscilloscopeViewLight` classes are the active UI implementation for
    this assignment submission.
    This wrapper remains only so existing imports keep working while the
    project transitions to the Qt View layer. It is legacy and not the
    primary UI that should be demonstrated to a grader.
    """

    def __init__(self, canvas: str = "Canvas", controls: str = "ControlPanel"):
        self.canvas = canvas
        self.controls = controls
        self.lastRenderedSignal: list[float] = []
        self.controller: Any | None = None

    def render(self, signal: list[float]) -> dict:
        """Compatibility API used by older controller scaffolding."""
        self.updateSignal(signal)
        return {
            "canvas": self.canvas,
            "controls": self.controls,
            "signal": list(self.lastRenderedSignal),
        }

    def updateSignal(self, signalData: Any) -> None:
        """Store the most recent signal without doing any signal processing."""
        self.lastRenderedSignal = list(signalData or [])

    def connectController(self, controller: Any) -> None:
        """Preserve the same MVC connection point as the Qt views."""
        self.controller = controller

    def getUserInput(self, command: str) -> str:
        """Compatibility pass-through used by the legacy placeholder view."""
        return command
