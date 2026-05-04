from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from ._ftdi_session import ioFtdiSession


class ioAbstractSessionBackedByteStream(ABC):
    def __init__(
        self,
        *,
        device_index: int = 0,
        dll_path: str | None = None,
        session_factory: Callable[[], object] | None = None,
    ):
        self.device_index = device_index
        self.dll_path = dll_path
        self.session_factory = session_factory or (
            lambda: ioFtdiSession(dll_path=self.dll_path, device_index=self.device_index)
        )
        self.session: object | None = None
        self.connected = False

    def open(self) -> None:
        session = self.session_factory()
        if hasattr(session, "open"):
            session.open()
            self._initialize_non_context_session(session)
        elif hasattr(session, "__enter__"):
            session = session.__enter__()
        else:
            raise AttributeError("session_factory must return an object with open() or __enter__().")
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

    def is_connected(self) -> bool:
        return self.connected

    @abstractmethod
    def _initialize_non_context_session(self, session: object) -> None:
        raise NotImplementedError


AbstractSessionBackedByteStream = ioAbstractSessionBackedByteStream
