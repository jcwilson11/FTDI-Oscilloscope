from __future__ import annotations

from .io_abstract_file_backed_byte_stream import ioAbstractFileBackedByteStream
from .io_abstract_readable_byte_stream import ioAbstractReadableByteStream


class ioFileInputByteStream(ioAbstractReadableByteStream, ioAbstractFileBackedByteStream):
    def __init__(self, input_path: str):
        self.input_path = input_path
        self.exhausted = False
        super().__init__(input_path)

    def _open_mode(self) -> str:
        return "rb"

    def _after_open(self) -> None:
        self.exhausted = False

    def _has_active_read_target(self) -> bool:
        return self.file_handle is not None

    def _read_bytes_impl(self, count: int) -> bytes:
        data = self.file_handle.read(count)
        if not data:
            self.exhausted = True
        return data

    def is_exhausted(self) -> bool:
        return self.exhausted


FileInputByteStream = ioFileInputByteStream
