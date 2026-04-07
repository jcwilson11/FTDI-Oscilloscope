from __future__ import annotations

from ._operation import ioBaseIoOperation
from .buffer import ioBuffer
from .errors import ioLibraryError


class ioWrite(ioBaseIoOperation):
    """Write M bytes from an external ioBuffer at a fixed frequency."""

    def __init__(
        self,
        buffer: ioBuffer | None = None,
        length: int | None = None,
        frequency_hz: float | None = None,
        *,
        device_index: int = 0,
        dll_path: str | None = None,
        session_factory=None,
    ):
        self.mBytes: int | None = None
        super().__init__(
            buffer,
            frequency_hz,
            device_index=device_index,
            dll_path=dll_path,
            session_factory=session_factory,
        )
        if length is not None:
            self.setM(length)

    def setM(self, length: int):
        if length <= 0:
            raise ioLibraryError("length must be greater than zero")
        self.mBytes = int(length)
        if self.buffer is not None and self.mBytes > self.buffer.size:
            raise ioLibraryError("length cannot exceed buffer size")
        return self

    def setBuffer(self, buffer: ioBuffer):
        super().setBuffer(buffer)
        if self.mBytes is not None and self.mBytes > buffer.size:
            raise ioLibraryError("length cannot exceed buffer size")
        return self

    @property
    def length(self) -> int | None:
        return self.mBytes

    def write_once(self) -> int:
        self._validate_configuration()
        with self._session_factory() as session:
            return session.write_bytes(self._require_buffer().read(self.mBytes))

    @property
    def element_interval_seconds(self) -> float:
        self._validate_configuration()
        return self.interval_seconds / self.mBytes

    def start_sequence(self, cycles: int) -> int:
        return self.run_sequence(cycles)

    def executeWrite(self, cycles: int | None = 1, *, sequence_mode: bool = False):
        if sequence_mode:
            return self.start_sequence(cycles if cycles is not None else 1)
        if cycles == 1:
            return self.write_once()
        return self.start(cycles=cycles)

    def run_sequence(self, cycles: int) -> int:
        if cycles < 0:
            raise ioLibraryError("cycles must be non-negative")

        self._validate_configuration()
        self._stop_event.clear()
        completed_cycles = 0
        with self._session_factory() as session:
            while not self._stop_event.is_set():
                self._write_sequence_cycle(session)
                completed_cycles += 1
                if completed_cycles >= cycles:
                    break
        return completed_cycles

    def _execute_cycle(self, session):
        session.write_bytes(self._require_buffer().read(self.mBytes))

    def _write_sequence_cycle(self, session):
        for index in range(self.mBytes):
            if self._stop_event.is_set():
                break
            session.write_bytes(self._require_buffer().read(1, start=index))
            if index < self.mBytes - 1:
                if self._stop_event.wait(self.element_interval_seconds):
                    break
        if not self._stop_event.is_set():
            self._stop_event.wait(self.element_interval_seconds)

    def _validate_configuration(self):
        buffer = self._require_buffer()
        self._require_frequency()
        if self.mBytes is None:
            raise ioLibraryError("length must be configured before execution")
        if self.mBytes > buffer.size:
            raise ioLibraryError("length cannot exceed buffer size")
