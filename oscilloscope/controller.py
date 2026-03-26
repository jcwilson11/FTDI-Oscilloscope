from __future__ import annotations

from .filters import FilterPipeline, ISignalFilter
from .model import OscilloscopeModel
from .view import OscilloscopeView


class OscilloscopeController:
    """Owns the model and view and coordinates rendering updates."""

    def __init__(
        self,
        *,
        filters: list[ISignalFilter] | None = None,
        canvas: str = "Canvas",
        controls: str = "ControlPanel",
    ):
        pipeline = FilterPipeline(filters)
        self.model = OscilloscopeModel(pipeline=pipeline)
        self.view = OscilloscopeView(canvas=canvas, controls=controls)

    def start(self, signal: list[float] | None = None) -> dict:
        if signal is None:
            signal = []
        return self.handleUserInput(signal)

    def handleUserInput(self, signal: list[float]) -> dict:
        processed_signal = self.model.setRawSignal(signal)
        return self.view.render(processed_signal)
