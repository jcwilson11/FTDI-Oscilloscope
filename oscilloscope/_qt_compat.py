from __future__ import annotations

from abc import ABCMeta
import sys

QT_IMPORT_ERROR = ""
PLOT_IMPORT_ERROR = ""

try:
    from PySide6 import QtCore, QtWidgets

    QT_AVAILABLE = True
except Exception as exc:  # pragma: no cover - dependency controlled by environment
    QtCore = None
    QtWidgets = None
    QT_AVAILABLE = False
    QT_IMPORT_ERROR = str(exc)

try:
    import pyqtgraph as pg

    PLOT_AVAILABLE = True
except Exception as exc:  # pragma: no cover - dependency controlled by environment
    pg = None
    PLOT_AVAILABLE = False
    PLOT_IMPORT_ERROR = str(exc)


if QT_AVAILABLE:
    def ensure_qt_application():
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
        return app

    class ioQtViewMeta(type(QtWidgets.QWidget), ABCMeta):
        """Combine Qt and ABC behavior for concrete view classes."""


else:
    def ensure_qt_application():
        return None

    class ioQtViewMeta(ABCMeta):
        """Fallback metaclass when Qt is unavailable."""
