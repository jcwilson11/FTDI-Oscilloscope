from __future__ import annotations

from .io_abstract_readable_byte_stream import ioAbstractReadableByteStream
from .io_abstract_session_backed_byte_stream import ioAbstractSessionBackedByteStream


class ioFtdiByteStream(ioAbstractReadableByteStream, ioAbstractSessionBackedByteStream):
    def __init__(self, *args, prefer_latest: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefer_latest = bool(prefer_latest)

    def _initialize_non_context_session(self, session: object) -> None:
        session.initialize_bitbang(direction_mask=0x00)

    def _has_active_read_target(self) -> bool:
        return self.session is not None

    def _read_bytes_impl(self, count: int) -> bytes:
        if self.prefer_latest and hasattr(self.session, "latest_read_bytes"):
            return self.session.latest_read_bytes(count)
        if hasattr(self.session, "queued_read_bytes"):
            return self.session.queued_read_bytes(count)
        return self.session.read_bytes(count)

    def is_exhausted(self) -> bool:
        return False


FtdiByteStream = ioFtdiByteStream
