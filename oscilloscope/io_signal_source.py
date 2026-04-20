from __future__ import annotations

from typing import Protocol, runtime_checkable

from .io_control_state import ioControlState


@runtime_checkable
class ioSignalSource(Protocol):
    def supports(self, input_source: str) -> bool:
        ...

    def generate(self, control_state: ioControlState) -> list[float]:
        ...


SignalSource = ioSignalSource
