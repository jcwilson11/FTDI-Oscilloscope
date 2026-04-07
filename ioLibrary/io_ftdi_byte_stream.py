from __future__ import annotations

from typing import Callable, Optional

from ._ftdi_session import ioFtdiSession


class ioFtdiByteStream:
    def __init__(
        self,
        *,
        device_index: int = 0,
        dll_path: str | None = None,
        session_factory: Optional[Callable[[], object]] = None,
    ):
        self.device_index = device_index
        self.dll_path = dll_path
        self.session_factory = session_factory or (
            lambda: ioFtdiSession(dll_path=self.dll_path, device_index=self.device_index)
        )
        self.session = None
        self.connected = False

    def open(self) -> None:
        session = self.session_factory()
        if hasattr(session, "__enter__"):
            session = session.__enter__()
        else:
            session.open()
            session.initialize_bitbang()
        self.session = session
        self.connected = True

    def close(self) -> None:
        if self.session is None:
            self.connected = False
            return

        try:
            if hasattr(self.session, "__exit__"):
                self.session.__exit__(None, None, None)
            else:
                self.session.close()
        finally:
            self.session = None
            self.connected = False

    def read_bytes(self, count: int) -> bytes:
        if not self.connected or self.session is None:
            raise RuntimeError("Input stream is not open.")
        return self.session.read_bytes(count)

    def is_connected(self) -> bool:
        return self.connected

    def is_exhausted(self) -> bool:
        return False


FtdiByteStream = ioFtdiByteStream
