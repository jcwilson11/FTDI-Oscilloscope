from __future__ import annotations

from typing import ClassVar

from .io_view_theme import ioViewTheme


class ioLandscapeTheme(ioViewTheme):
    NAME: ClassVar[str] = "landscape"
    ORIENTATION: ClassVar[str] = "landscape"
    PALETTE: ClassVar[dict[str, str]] = {
        "background": "#eef4f7",
        "panel": "#ffffff",
        "accent": "#375a7f",
        "grid": "#aac4d4",
        "signal": "#5d2e8c",
        "text": "#10212b",
    }

    def getName(self) -> str:
        return self.NAME

    def getOrientation(self) -> str:
        return self.ORIENTATION

    def getPalette(self) -> dict[str, str]:
        return dict(self.PALETTE)
