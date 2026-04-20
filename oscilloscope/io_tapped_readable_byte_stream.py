from __future__ import annotations

from ioLibrary import ioReadableByteStream

from .io_live_sample_history import ioLiveSampleHistory


class ioTappedReadableByteStream:
    """Readable stream wrapper that mirrors incoming bytes into sample history."""

    def __init__(self, stream: ioReadableByteStream, history: ioLiveSampleHistory):
        self.stream = stream
        self.history = history

    def open(self) -> None:
        self.stream.open()

    def close(self) -> None:
        self.stream.close()

    def is_connected(self) -> bool:
        return self.stream.is_connected()

    def is_exhausted(self) -> bool:
        return self.stream.is_exhausted()

    def read_bytes(self, count: int) -> bytes:
        payload = self.stream.read_bytes(count)
        if payload:
            self.history.append_bytes(payload)
        return payload
