from __future__ import annotations

from .io_static_theme_base import ioStaticThemeBase


class ioPortraitTheme(ioStaticThemeBase):
    NAME = "portrait"
    ORIENTATION = "portrait"
    PALETTE = {
        "background": "#f6efe3",
        "panel": "#fffaf2",
        "accent": "#2d6a8a",
        "grid": "#c8b69b",
        "signal": "#bb3e03",
        "text": "#1f2933",
    }
