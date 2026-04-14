from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:  # pragma: no cover - allows non-UI imports before Qt is installed
    QtWidgets = None


if QtWidgets is not None:
    class _ioViewMeta(type(QtWidgets.QWidget), ABCMeta):
        """Combine Qt's widget metaclass with Python's ABC support."""


else:
    class _ioViewMeta(ABCMeta):
        """Fallback metaclass used when PySide6 is unavailable."""


class ioViewBase(metaclass=_ioViewMeta):
    """Abstract MVC View boundary for oscilloscope user interfaces.

    Concrete UI classes are responsible only for rendering controller-supplied
    signal data and forwarding user intent back to the controller.
    They must not perform FTDI I/O, file input, or waveform processing.
    """

    @abstractmethod
    def updateSignal(self, signalData: Any) -> None:
        """Render new signal data supplied by the controller."""
        raise NotImplementedError

    @abstractmethod
    def connectController(self, controller: Any) -> None:
        """Store a controller reference for UI event forwarding only."""
        raise NotImplementedError
