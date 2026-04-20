from __future__ import annotations

from .io_static_theme_base import ioStaticThemeBase


class ioLandscapeTheme(ioStaticThemeBase):
    NAME = "landscape"
    ORIENTATION = "landscape"
    PALETTE = {
        "background": "#eef4f7",
        "panel": "#ffffff",
        "accent": "#375a7f",
        "grid": "#aac4d4",
        "signal": "#5d2e8c",
        "text": "#10212b",
    }
