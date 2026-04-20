from typing import Protocol, runtime_checkable

from .io_stream_lifecycle import ioStreamLifecycle


@runtime_checkable
class ioWritableByteStream(ioStreamLifecycle, Protocol):
    def write_bytes(self, data: bytes) -> int:
        ...


WritableByteStream = ioWritableByteStream
