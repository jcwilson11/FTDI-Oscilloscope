from __future__ import annotations

from pathlib import Path


class ioLiveFileTailByteStream:
    """Readable byte stream that tails a file and resets on truncation."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.file_handle = None
        self.connected = False
        self._offset = 0

    def open(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self.file_handle = self.path.open("rb")
        self.connected = True
        self._offset = 0

    def close(self) -> None:
        if self.file_handle is not None:
            self.file_handle.close()
            self.file_handle = None
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def is_exhausted(self) -> bool:
        return False

    def read_bytes(self, count: int) -> bytes:
        if self.file_handle is None:
            raise RuntimeError("Input stream is not open.")

        current_size = self.path.stat().st_size if self.path.exists() else 0
        if current_size < self._offset:
            self.file_handle.seek(0)
            self._offset = 0

        self.file_handle.seek(self._offset)
        payload = self.file_handle.read(max(0, count))
        self._offset += len(payload)
        return payload
