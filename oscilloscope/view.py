"""Backward-compatible view import surface for older demos and tests.

The primary abstraction is ``ioOscilloscopeView``.
``OscilloscopeView`` remains mapped to the compact concrete Qt view.
"""

from .io_compact_oscilloscope_view import ioCompactOscilloscopeView
from .io_oscilloscope_view import ioOscilloscopeView

OscilloscopeView = ioCompactOscilloscopeView

__all__ = ["OscilloscopeView", "ioOscilloscopeView"]
