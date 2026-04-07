from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import Callable

from ._ftdi_session import ioFtdiSession
from .buffer import ioBuffer
from .errors import ioLibraryError


class ioBaseIoOperation(ABC):
    def __init__(
        self,
        buffer: ioBuffer | None = None,
        frequency_hz: float | None = None,
        *,
        device_index: int = 0,
        dll_path: str | None = None,
        session_factory: Callable[[], object] | None = None,
    ):
        self.buffer: ioBuffer | None = None
        self.frequency_hz: float | None = None
        self.device_index = device_index
        self.dll_path = dll_path
        self._session_factory = session_factory or (
            lambda: ioFtdiSession(dll_path=self.dll_path, device_index=self.device_index)
        )
        self._stop_event = threading.Event()

        if buffer is not None:
            self.setBuffer(buffer)
        if frequency_hz is not None:
            self.setFrequency(frequency_hz)

    def setBuffer(self, buffer: ioBuffer):
        if not isinstance(buffer, ioBuffer):
            raise ioLibraryError("buffer must be an ioBuffer instance")
        self.buffer = buffer
        return self

    def setFrequency(self, frequency_hz: float):
        if frequency_hz <= 0:
            raise ioLibraryError("frequency_hz must be greater than zero")
        self.frequency_hz = float(frequency_hz)
        return self

    def _require_buffer(self) -> ioBuffer:
        if self.buffer is None:
            raise ioLibraryError("buffer must be configured before execution")
        return self.buffer

    def _require_frequency(self) -> float:
        if self.frequency_hz is None:
            raise ioLibraryError("frequency_hz must be configured before execution")
        return self.frequency_hz

    @property
    def interval_seconds(self) -> float:
        return 1.0 / self._require_frequency()

    def stop(self):
        self._stop_event.set()

    def start(self, cycles: int | None = None) -> int:
        return self.run(cycles=cycles)

    def run(self, cycles: int | None = None) -> int:
        if cycles is not None and cycles < 0:
            raise ioLibraryError("cycles must be non-negative")

        self._validate_configuration()
        self._stop_event.clear()
        completed_cycles = 0
        with self._session_factory() as session:
            while not self._stop_event.is_set():
                self._execute_cycle(session)
                completed_cycles += 1
                if cycles is not None and completed_cycles >= cycles:
                    break
                if self._stop_event.wait(self.interval_seconds):
                    break
        return completed_cycles

    @abstractmethod
    def _execute_cycle(self, session):
        raise NotImplementedError

    @abstractmethod
    def _validate_configuration(self):
        raise NotImplementedError


_BaseIoOperation = ioBaseIoOperation
