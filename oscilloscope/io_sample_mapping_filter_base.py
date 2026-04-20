from __future__ import annotations

from abc import ABC, abstractmethod

from .io_signal_filter import ioSignalFilter


class ioSampleMappingFilterBase(ioSignalFilter, ABC):
    FILTER_NAME = ""

    def apply(self, data: list[float]) -> list[float]:
        return [self._transform_sample(sample) for sample in data]

    def getName(self) -> str:
        return self.FILTER_NAME

    @abstractmethod
    def _transform_sample(self, sample: float) -> float:
        raise NotImplementedError


SampleMappingFilterBase = ioSampleMappingFilterBase
