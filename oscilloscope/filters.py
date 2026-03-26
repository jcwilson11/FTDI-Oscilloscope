from __future__ import annotations

from abc import ABC, abstractmethod


class ISignalFilter(ABC):
    """Interface contract for all signal-processing filters."""

    @abstractmethod
    def apply(self, data: list[float]) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    def getName(self) -> str:
        raise NotImplementedError


class FilterPipeline:
    """Processes signal data through an ordered set of filters."""

    def __init__(self, filters: list[ISignalFilter] | None = None):
        self.filters: list[ISignalFilter] = list(filters or [])

    def addFilter(self, signal_filter: ISignalFilter):
        self.filters.append(signal_filter)
        return self

    def process(self, data: list[float]) -> list[float]:
        processed = list(data)
        for signal_filter in self.filters:
            processed = signal_filter.apply(processed)
        return processed


class scpScale(ISignalFilter):
    def __init__(self, scaleFactor: float):
        self.scaleFactor = scaleFactor

    def apply(self, data: list[float]) -> list[float]:
        return [sample * self.scaleFactor for sample in data]

    def getName(self) -> str:
        return "scpScale"


class scpOffset(ISignalFilter):
    def __init__(self, offsetValue: float):
        self.offsetValue = offsetValue

    def apply(self, data: list[float]) -> list[float]:
        return [sample + self.offsetValue for sample in data]

    def getName(self) -> str:
        return "scpOffset"
