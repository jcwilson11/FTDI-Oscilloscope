from __future__ import annotations

from ._operation import _BaseIoOperation
from .buffer import ioBuffer
from .errors import IoLibraryError


class ioRead(_BaseIoOperation):
    """Read N bytes from FTDI into an external ioBuffer at a fixed frequency."""

    def __init__(
        self,
        buffer: ioBuffer | None = None,
        byte_count: int | None = None,
        frequency_hz: float | None = None,
        *,
        device_index: int = 0,
        dll_path: str | None = None,
        session_factory=None,
    ):
        self.nBytes: int | None = None
        super().__init__(
            buffer,
            frequency_hz,
            device_index=device_index,
            dll_path=dll_path,
            session_factory=session_factory,
        )
        if byte_count is not None:
            self.setN(byte_count)

    def setN(self, byte_count: int):
        if byte_count <= 0:
            raise IoLibraryError("byte_count must be greater than zero")
        self.nBytes = int(byte_count)
        if self.buffer is not None and self.nBytes > self.buffer.size:
            raise IoLibraryError("byte_count cannot exceed buffer size")
        return self

    def setBuffer(self, buffer: ioBuffer):
        super().setBuffer(buffer)
        if self.nBytes is not None and self.nBytes > buffer.size:
            raise IoLibraryError("byte_count cannot exceed buffer size")
        return self

    @property
    def byte_count(self) -> int | None:
        return self.nBytes

    def executeRead(self, cycles: int | None = 1):
        if cycles == 1:
            return self.read_once()
        return self.start(cycles=cycles)

    def read_once(self) -> bytes:
        self._validate_configuration()
        with self._session_factory() as session:
            data = session.read_bytes(self.nBytes)
            self._require_buffer().write(data)
            return data

    def _execute_cycle(self, session):
        data = session.read_bytes(self.nBytes)
        self._require_buffer().write(data)

    def _validate_configuration(self):
        buffer = self._require_buffer()
        self._require_frequency()
        if self.nBytes is None:
            raise IoLibraryError("byte_count must be configured before execution")
        if self.nBytes > buffer.size:
            raise IoLibraryError("byte_count cannot exceed buffer size")
