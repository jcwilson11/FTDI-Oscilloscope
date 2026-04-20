from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO


class ioAbstractFileBackedByteStream(ABC):
    def __init__(self, path: str):
        self._path = path
        self.file_handle: BinaryIO | None = None
        self.connected = False

    def open(self) -> None:
        self.file_handle = open(self._path, self._open_mode())
        self.connected = True
        self._after_open()

    def close(self) -> None:
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def _after_open(self) -> None:
        pass

    @abstractmethod
    def _open_mode(self) -> str:
        raise NotImplementedError


AbstractFileBackedByteStream = ioAbstractFileBackedByteStream
