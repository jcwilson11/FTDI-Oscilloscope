"""MVC + Pipe-and-Filter oscilloscope architecture implementation."""

from .controller import OscilloscopeController
from .filters import FilterPipeline, ISignalFilter, scpOffset, scpScale
from .model import OscilloscopeModel
from .view import OscilloscopeView

__all__ = [
    "FilterPipeline",
    "ISignalFilter",
    "OscilloscopeController",
    "OscilloscopeModel",
    "OscilloscopeView",
    "scpOffset",
    "scpScale",
]
