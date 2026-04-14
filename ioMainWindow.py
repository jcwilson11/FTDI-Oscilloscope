"""Qt main window for the assignment's active oscilloscope View layer."""

from __future__ import annotations

from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from .ioOscilloscopeViewDark import ioOscilloscopeViewDark
from .ioOscilloscopeViewLight import ioOscilloscopeViewLight
from .ioViewBase import ioViewBase


class ioMainWindow(QtWidgets.QMainWindow):
    """Hosts the active oscilloscope view and forwards UI-only actions.

    This is the primary Qt container for the assignment submission.
    It keeps the UI minimal by exposing only:
    - the waveform display area
    - theme selection (`Dark` / `Light`)
    - data source selection (`FTDI Device` / `File Input`)

    Expected controller integration:
    - `setDataSource(source_name: str)` to respond to the UI source selector
    - `setTheme(theme_name: str)` if the controller wants to track the active theme
    - `updateSignal(signal_data)` is called by the controller on this window

    This window never reads files, talks to FTDI devices, or processes signal data.
    It is only a UI shell that forwards user selections to the controller and
    routes controller-provided signal data to the currently active View.
    """

    dataSourceChanged = QtCore.Signal(str)
    themeChanged = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._controller: Any | None = None

        self._darkView = ioOscilloscopeViewDark()
        self._lightView = ioOscilloscopeViewLight()

        self._stack = QtWidgets.QStackedWidget()
        self._stack.addWidget(self._darkView)
        self._stack.addWidget(self._lightView)

        self._themeSelector = QtWidgets.QComboBox()
        self._themeSelector.addItems(["Dark", "Light"])
        self._themeSelector.setMinimumWidth(120)
        self._themeSelector.currentTextChanged.connect(self._handleThemeSelectionChanged)

        self._sourceSelector = QtWidgets.QComboBox()
        self._sourceSelector.addItems(["FTDI Device", "File Input"])
        self._sourceSelector.setMinimumWidth(140)
        self._sourceSelector.currentTextChanged.connect(self._handleDataSourceChanged)

        selectorLayout = QtWidgets.QHBoxLayout()
        selectorLayout.setContentsMargins(12, 12, 12, 0)
        selectorLayout.addStretch()
        selectorLayout.addWidget(self._themeSelector)
        selectorLayout.addWidget(self._sourceSelector)

        centralWidget = QtWidgets.QWidget()
        contentLayout = QtWidgets.QVBoxLayout(centralWidget)
        contentLayout.setContentsMargins(0, 0, 0, 0)
        contentLayout.setSpacing(8)
        contentLayout.addLayout(selectorLayout)
        contentLayout.addWidget(self._stack)

        self.setCentralWidget(centralWidget)
        self.setWindowTitle("FTDI Oscilloscope")
        self.resize(1100, 700)

        self._installShortcuts()
        self._applyWindowTheme("dark")

    def _installShortcuts(self) -> None:
        toggleThemeShortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+T"), self)
        toggleThemeShortcut.activated.connect(self.toggleTheme)

    def connectController(self, controller: Any) -> None:
        """Bind the controller so UI events can be forwarded without business logic."""
        self._controller = controller
        self._darkView.connectController(controller)
        self._lightView.connectController(controller)

    def updateSignal(self, signalData: Any) -> None:
        """Forward controller-provided signal data to the active Qt View."""
        view = self.activeView()
        view.updateSignal(signalData)

    def activeView(self) -> ioViewBase:
        currentWidget = self._stack.currentWidget()
        if not isinstance(currentWidget, ioViewBase):
            raise TypeError("Active stacked widget does not implement ioViewBase.")
        return currentWidget

    def toggleTheme(self) -> None:
        nextTheme = "light" if self._stack.currentWidget() is self._darkView else "dark"
        self.setTheme(nextTheme)

    def setTheme(self, themeName: str) -> None:
        """Switch between the assignment's two selectable Qt views."""
        normalizedTheme = themeName.strip().lower()
        if normalizedTheme == "light":
            self._stack.setCurrentWidget(self._lightView)
            self._themeSelector.blockSignals(True)
            self._themeSelector.setCurrentText("Light")
            self._themeSelector.blockSignals(False)
        else:
            normalizedTheme = "dark"
            self._stack.setCurrentWidget(self._darkView)
            self._themeSelector.blockSignals(True)
            self._themeSelector.setCurrentText("Dark")
            self._themeSelector.blockSignals(False)

        self._applyWindowTheme(normalizedTheme)
        self.themeChanged.emit(normalizedTheme)
        if self._controller is not None and hasattr(self._controller, "setTheme"):
            self._controller.setTheme(normalizedTheme)

    def _applyWindowTheme(self, themeName: str) -> None:
        if themeName == "light":
            self.setStyleSheet(
                """
                QMainWindow {
                    background-color: #f1f5f9;
                }
                QComboBox {
                    padding: 6px 10px;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    background-color: #ffffff;
                    color: #0f172a;
                }
                """
            )
            return

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #020617;
            }
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #334155;
                border-radius: 6px;
                background-color: #0f172a;
                color: #e2e8f0;
            }
            """
        )

    @QtCore.Slot(str)
    def _handleDataSourceChanged(self, sourceName: str) -> None:
        """Emit the selected source and forward intent to the controller."""
        self.dataSourceChanged.emit(sourceName)
        if self._controller is not None and hasattr(self._controller, "setDataSource"):
            self._controller.setDataSource(sourceName)

    @QtCore.Slot(str)
    def _handleThemeSelectionChanged(self, themeLabel: str) -> None:
        """Update the active Qt view when the user changes the theme selector."""
        self.setTheme(themeLabel)
