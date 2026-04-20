from __future__ import annotations

from .io_signal_filter import ioSignalFilter


class ioFilterPipeline:
    """Processes signal data through an ordered set of filters."""

    def __init__(self, filters: list[ioSignalFilter] | None = None):
        self.filters: list[ioSignalFilter] = list(filters or [])

    def addFilter(self, signal_filter: ioSignalFilter) -> "ioFilterPipeline":
        self.filters.append(signal_filter)
        return self

    def setFilters(self, filters: list[ioSignalFilter]) -> "ioFilterPipeline":
        self.filters = list(filters)
        return self

    def process(self, data: list[float]) -> list[float]:
        processed = list(data)
        for signal_filter in self.filters:
            processed = signal_filter.apply(processed)
        return processed


FilterPipeline = ioFilterPipeline
