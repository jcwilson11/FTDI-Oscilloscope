from typing import Protocol


class ioReadableByteStream(Protocol):
    def open(self) -> None:
        ...

    def close(self) -> None:
        ...

    def read_bytes(self, count: int) -> bytes:
        ...

    def is_connected(self) -> bool:
        ...

    def is_exhausted(self) -> bool:
        ...


ReadableByteStream = ioReadableByteStream
