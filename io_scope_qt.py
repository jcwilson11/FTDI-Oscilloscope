from __future__ import annotations

import sys
from pathlib import Path

from oscilloscope import (
    QT_AVAILABLE,
    QT_IMPORT_ERROR,
    ioCompactOscilloscopeView,
    ioDetailedOscilloscopeView,
    ioOscilloscopeController,
    ioQtScopeWindow,
    ioScopeSettingsStore,
)


def run_scope_qt(*, headless: bool = False, settings_path: str | Path | None = None) -> int:
    app = None
    owns_app = False
    if QT_AVAILABLE:
        from PySide6 import QtWidgets

        app = QtWidgets.QApplication.instance()
        owns_app = app is None
        if owns_app:
            app = QtWidgets.QApplication(sys.argv)

    views = [ioCompactOscilloscopeView(), ioDetailedOscilloscopeView()]
    controller = ioOscilloscopeController(views=views)
    settings_store = ioScopeSettingsStore(settings_path)
    controller.importPersistentState(settings_store.load())
    controller.addStateChangeListener(settings_store.save)
    settings_store.save(controller.exportPersistentState())
    window = ioQtScopeWindow(views=views)
    window.connectController(controller)
    window.setActiveView(controller.model.controlState.active_view)

    if headless or not QT_AVAILABLE:
        if not QT_AVAILABLE and not headless:
            detail = f" Details: {QT_IMPORT_ERROR}" if QT_IMPORT_ERROR else ""
            print(
                "Qt UI dependencies are unavailable. Install PySide6 and pyqtgraph, "
                "or use --headless for a non-visual smoke test."
                f"{detail}",
                file=sys.stderr,
            )
            return 1
        print(
            f"Qt scope window initialized in headless mode with active view "
            f"'{window.activeViewId()}'."
        )
        return 0

    window.show()
    exit_code = app.exec()
    return int(exit_code) if owns_app else 0
