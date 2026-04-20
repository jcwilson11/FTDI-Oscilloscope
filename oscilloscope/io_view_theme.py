from __future__ import annotations

from abc import ABC, abstractmethod


class ioViewTheme(ABC):
    @abstractmethod
    def getName(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def getOrientation(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def getPalette(self) -> dict[str, str]:
        raise NotImplementedError
