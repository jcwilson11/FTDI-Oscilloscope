from typing import Protocol


class ioWritableByteStream(Protocol):
    def open(self) -> None:
        ...

    def close(self) -> None:
        ...

    def write_bytes(self, data: bytes) -> int:
        ...

    def is_connected(self) -> bool:
        ...


WritableByteStream = ioWritableByteStream
