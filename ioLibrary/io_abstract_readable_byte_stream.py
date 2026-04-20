from __future__ import annotations

from abc import ABC, abstractmethod


class ioAbstractReadableByteStream(ABC):
    def read_bytes(self, count: int) -> bytes:
        self._ensure_readable()
        return self._read_bytes_impl(count)

    def is_exhausted(self) -> bool:
        return False

    def _ensure_readable(self) -> None:
        if not self._is_connected_state() or not self._has_active_read_target():
            raise RuntimeError("Input stream is not open.")

    def _is_connected_state(self) -> bool:
        return bool(self.is_connected())

    @abstractmethod
    def _has_active_read_target(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _read_bytes_impl(self, count: int) -> bytes:
        raise NotImplementedError


AbstractReadableByteStream = ioAbstractReadableByteStream
