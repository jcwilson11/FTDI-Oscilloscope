from __future__ import annotations

from .filters import FilterPipeline


class OscilloscopeModel:
    """Stores raw signal state and applies the filter pipeline."""

    def __init__(self, pipeline: FilterPipeline | None = None):
        self.rawSignal: list[float] = []
        self.processedSignal: list[float] = []
        self.pipeline = pipeline if pipeline is not None else FilterPipeline()

    def setRawSignal(self, signal: list[float]) -> list[float]:
        self.rawSignal = list(signal)
        self.processedSignal = self.pipeline.process(self.rawSignal)
        return self.processedSignal

    def getProcessedSignal(self) -> list[float]:
        return list(self.processedSignal)
