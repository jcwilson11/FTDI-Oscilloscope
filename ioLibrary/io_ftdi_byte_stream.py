from __future__ import annotations

from .io_abstract_readable_byte_stream import ioAbstractReadableByteStream
from .io_abstract_session_backed_byte_stream import ioAbstractSessionBackedByteStream


class ioFtdiByteStream(ioAbstractReadableByteStream, ioAbstractSessionBackedByteStream):
    def _initialize_non_context_session(self, session: object) -> None:
        session.initialize_bitbang()

    def _has_active_read_target(self) -> bool:
        return self.session is not None

    def _read_bytes_impl(self, count: int) -> bytes:
        return self.session.read_bytes(count)

    def is_exhausted(self) -> bool:
        return False


FtdiByteStream = ioFtdiByteStream
