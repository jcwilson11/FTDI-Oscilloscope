from __future__ import annotations

from .io_abstract_session_backed_byte_stream import ioAbstractSessionBackedByteStream
from .io_abstract_writable_byte_stream import ioAbstractWritableByteStream


class ioFtdiOutputByteStream(ioAbstractWritableByteStream, ioAbstractSessionBackedByteStream):
    def _initialize_non_context_session(self, session: object) -> None:
        if hasattr(session, "initialize_bitbang"):
            session.initialize_bitbang()

    def _has_active_write_target(self) -> bool:
        return self.session is not None

    def _write_bytes_impl(self, data: bytes) -> int:
        return self.session.write_bytes(data)


FtdiOutputByteStream = ioFtdiOutputByteStream
