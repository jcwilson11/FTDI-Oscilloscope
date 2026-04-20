from __future__ import annotations

from abc import ABC
from typing import ClassVar

from .io_view_theme import ioViewTheme


class ioStaticThemeBase(ioViewTheme, ABC):
    NAME: ClassVar[str] = ""
    ORIENTATION: ClassVar[str] = ""
    PALETTE: ClassVar[dict[str, str]] = {}

    def getName(self) -> str:
        return self.NAME

    def getOrientation(self) -> str:
        return self.ORIENTATION

    def getPalette(self) -> dict[str, str]:
        return dict(self.PALETTE)


StaticThemeBase = ioStaticThemeBase
