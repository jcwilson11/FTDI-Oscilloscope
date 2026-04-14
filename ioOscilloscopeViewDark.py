"""Dark-theme Qt oscilloscope View used by the assignment UI."""

from __future__ import annotations

from typing import Any

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets

from .ioViewBase import ioViewBase


class ioOscilloscopeViewDark(ioViewBase, QtWidgets.QWidget):
    """Dark Qt View that renders waveform data without backend responsibilities.

    The controller supplies signal data by calling `updateSignal(signalData)`.
    This view does not access FTDI devices, read files, or process waveform data.
    """

    _plotRequested = QtCore.Signal(object)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._controller: Any | None = None
        self._lastSignal = np.array([], dtype=float)

        self._plotWidget = pg.PlotWidget()
        self._curve = self._plotWidget.plot(
            pen=pg.mkPen(color="#00e5ff", width=2),
            antialias=True,
        )

        self._configurePlot()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plotWidget)

        self._plotRequested.connect(
            self._applySignal,
            QtCore.Qt.ConnectionType.QueuedConnection,
        )

    def _configurePlot(self) -> None:
        self.setObjectName("ioOscilloscopeViewDark")
        self.setStyleSheet(
            """
            QWidget#ioOscilloscopeViewDark {
                background-color: #0b1020;
            }
            """
        )

        self._plotWidget.setBackground("#0b1020")
        self._plotWidget.showGrid(x=True, y=True, alpha=0.25)
        self._plotWidget.setMenuEnabled(False)
        self._plotWidget.setMouseEnabled(x=False, y=False)
        self._plotWidget.hideButtons()
        self._plotWidget.setLabel("left", "Amplitude", color="#94a3b8")
        self._plotWidget.setLabel("bottom", "Samples", color="#94a3b8")

        plotItem = self._plotWidget.getPlotItem()
        if plotItem is not None:
            plotItem.getAxis("left").setPen(pg.mkPen("#334155"))
            plotItem.getAxis("bottom").setPen(pg.mkPen("#334155"))
            plotItem.getAxis("left").setTextPen(pg.mkPen("#94a3b8"))
            plotItem.getAxis("bottom").setTextPen(pg.mkPen("#94a3b8"))

    def connectController(self, controller: Any) -> None:
        """Store the controller for future UI event wiring only."""
        self._controller = controller

    def updateSignal(self, signalData: Any) -> None:
        """Queue a redraw request so controller updates remain UI-thread safe."""
        self._plotRequested.emit(signalData)

    @QtCore.Slot(object)
    def _applySignal(self, signalData: Any) -> None:
        if signalData is None:
            signal = np.array([], dtype=float)
        else:
            signal = np.asarray(signalData, dtype=float).ravel()

        self._lastSignal = signal
        xAxis = np.arange(signal.size, dtype=float)
        self._curve.setData(xAxis, signal)
