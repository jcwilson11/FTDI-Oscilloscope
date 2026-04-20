from typing import Protocol, runtime_checkable

from .io_stream_lifecycle import ioStreamLifecycle


@runtime_checkable
class ioReadableByteStream(ioStreamLifecycle, Protocol):
    def read_bytes(self, count: int) -> bytes:
        ...

    def is_exhausted(self) -> bool:
        ...


ReadableByteStream = ioReadableByteStream
