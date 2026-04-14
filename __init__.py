"""MVC + Pipe-and-Filter oscilloscope architecture implementation."""

from .controller import OscilloscopeController
from .filters import FilterPipeline, ISignalFilter, scpOffset, scpScale
from .model import OscilloscopeModel
from .view import OscilloscopeView
from .ioViewBase import ioViewBase

try:
    from .ioMainWindow import ioMainWindow
    from .ioOscilloscopeViewDark import ioOscilloscopeViewDark
    from .ioOscilloscopeViewLight import ioOscilloscopeViewLight
except ModuleNotFoundError:
    # Keep the non-UI oscilloscope package importable when Qt dependencies
    # are not installed yet. UI modules can still be imported directly once
    # PySide6 and pyqtgraph are available.
    ioMainWindow = None
    ioOscilloscopeViewDark = None
    ioOscilloscopeViewLight = None

__all__ = [
    "FilterPipeline",
    "ISignalFilter",
    "OscilloscopeController",
    "OscilloscopeModel",
    "OscilloscopeView",
    "ioMainWindow",
    "ioOscilloscopeViewDark",
    "ioOscilloscopeViewLight",
    "ioViewBase",
    "scpOffset",
    "scpScale",
]
