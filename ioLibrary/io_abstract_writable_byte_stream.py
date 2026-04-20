from __future__ import annotations

from abc import ABC, abstractmethod


class ioAbstractWritableByteStream(ABC):
    def write_bytes(self, data: bytes) -> int:
        self._ensure_writable()
        return self._write_bytes_impl(data)

    def _ensure_writable(self) -> None:
        if not self._is_connected_state() or not self._has_active_write_target():
            raise RuntimeError("Output stream is not open.")

    def _is_connected_state(self) -> bool:
        return bool(self.is_connected())

    @abstractmethod
    def _has_active_write_target(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _write_bytes_impl(self, data: bytes) -> int:
        raise NotImplementedError


AbstractWritableByteStream = ioAbstractWritableByteStream
