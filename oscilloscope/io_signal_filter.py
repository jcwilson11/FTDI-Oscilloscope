from __future__ import annotations

from abc import ABC, abstractmethod


class ioSignalFilter(ABC):
    """Interface contract for signal-processing filters."""

    @abstractmethod
    def apply(self, data: list[float]) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    def getName(self) -> str:
        raise NotImplementedError


ISignalFilter = ioSignalFilter
