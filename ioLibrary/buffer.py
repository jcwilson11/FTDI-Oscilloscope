from __future__ import annotations

from .errors import IoLibraryError


class ioBuffer:
    """Shared byte buffer aggregated by ioRead and ioWrite."""

    def __init__(self, size: int, initial_data: bytes | bytearray | list[int] | None = None):
        if size <= 0:
            raise IoLibraryError("size must be greater than zero")

        self._buffer = bytearray(size)
        if initial_data is not None:
            self.load(initial_data)

    @property
    def size(self) -> int:
        return len(self._buffer)

    def getSize(self) -> int:
        return self.size

    def load(self, data: bytes | bytearray | list[int], start: int = 0):
        if start < 0:
            raise IoLibraryError("start must be non-negative")

        payload = bytes(data)
        end = start + len(payload)
        if end > self.size:
            raise IoLibraryError("data does not fit in buffer")
        self._buffer[start:end] = payload

    def read(self, length: int | None = None, start: int = 0) -> bytes:
        if start < 0:
            raise IoLibraryError("start must be non-negative")
        if length is None:
            length = self.size - start
        if length < 0:
            raise IoLibraryError("length must be non-negative")

        end = start + length
        if end > self.size:
            raise IoLibraryError("requested range exceeds buffer size")
        return bytes(self._buffer[start:end])

    def write(self, data: bytes | bytearray | list[int], start: int = 0):
        self.load(data, start=start)

    def getRaw(self) -> bytearray:
        return self._buffer

    def to_list(self) -> list[int]:
        return list(self._buffer)
