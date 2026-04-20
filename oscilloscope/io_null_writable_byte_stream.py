from __future__ import annotations


class ioNullWritableByteStream:
    """Writable sink that discards bytes while preserving pipeline flow."""

    def __init__(self):
        self.connected = False

    def open(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def write_bytes(self, data: bytes) -> int:
        if not self.connected:
            raise RuntimeError("Output stream is not open.")
        return len(data)
