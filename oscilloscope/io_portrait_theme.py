from __future__ import annotations

from typing import ClassVar

from .io_view_theme import ioViewTheme


class ioPortraitTheme(ioViewTheme):
    NAME: ClassVar[str] = "portrait"
    ORIENTATION: ClassVar[str] = "portrait"
    PALETTE: ClassVar[dict[str, str]] = {
        "background": "#f6efe3",
        "panel": "#fffaf2",
        "accent": "#2d6a8a",
        "grid": "#c8b69b",
        "signal": "#bb3e03",
        "text": "#1f2933",
    }

    def getName(self) -> str:
        return self.NAME

    def getOrientation(self) -> str:
        return self.ORIENTATION

    def getPalette(self) -> dict[str, str]:
        return dict(self.PALETTE)
