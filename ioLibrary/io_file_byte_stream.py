from __future__ import annotations

from .io_abstract_file_backed_byte_stream import ioAbstractFileBackedByteStream
from .io_abstract_writable_byte_stream import ioAbstractWritableByteStream


class ioFileByteStream(ioAbstractWritableByteStream, ioAbstractFileBackedByteStream):
    def __init__(self, output_path: str, *, append: bool = True):
        self.output_path = output_path
        self.append = append
        super().__init__(output_path)

    def _open_mode(self) -> str:
        return "ab" if self.append else "wb"

    def _has_active_write_target(self) -> bool:
        return self.file_handle is not None

    def _write_bytes_impl(self, data: bytes) -> int:
        self.file_handle.write(data)
        self.file_handle.flush()
        return len(data)


FileByteStream = ioFileByteStream
