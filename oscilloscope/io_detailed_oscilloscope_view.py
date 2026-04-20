from __future__ import annotations

from typing import Any

from ._qt_compat import PLOT_AVAILABLE, QT_AVAILABLE, QtWidgets, ensure_qt_application, ioQtViewMeta, pg
from .io_landscape_theme import ioLandscapeTheme
from .io_oscilloscope_view import ioOscilloscopeView


_QtWidgetBase = QtWidgets.QWidget if QT_AVAILABLE else object


class ioDetailedOscilloscopeView(ioOscilloscopeView, _QtWidgetBase, metaclass=ioQtViewMeta):
    """Detailed Qt view focused on waveform visibility and runtime telemetry."""

    def __init__(self, parent=None):
        if QT_AVAILABLE:
            ensure_qt_application()
            QtWidgets.QWidget.__init__(self, parent)
        ioOscilloscopeView.__init__(
            self,
            view_id="detailed",
            title="Detailed Oscilloscope UI",
            theme=ioLandscapeTheme(),
            canvas="DetailedCanvas",
            controls="DetailedControls",
        )
        self._detail_lines: list[str] = []

        if QT_AVAILABLE:
            self._plotWidget = self._build_plot_widget()
            self._details = QtWidgets.QPlainTextEdit()
            self._details.setReadOnly(True)
            self._build_layout()

    def _build_plot_widget(self):
        if PLOT_AVAILABLE:
            plot_widget = pg.PlotWidget()
            self._curve = plot_widget.plot(
                pen=pg.mkPen(color=self.theme.getPalette()["signal"], width=2),
                antialias=True,
            )
            plot_widget.showGrid(x=True, y=True, alpha=0.35)
            plot_widget.setMenuEnabled(False)
            plot_widget.hideButtons()
            plot_widget.setYRange(-5.0, 5.0, padding=0.0)
            plot_widget.enableAutoRange(x=True, y=False)
            return plot_widget

        self._curve = None
        placeholder = QtWidgets.QLabel("Install pyqtgraph to enable live waveform plotting.")
        placeholder.setWordWrap(True)
        return placeholder

    def _build_layout(self) -> None:
        self.setObjectName("ioDetailedOscilloscopeView")
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self._plotWidget, 3)
        layout.addWidget(self._details, 2)
        self._apply_stylesheet()

    def _apply_stylesheet(self) -> None:
        if not QT_AVAILABLE:
            return
        palette = self.theme.getPalette()
        self.setStyleSheet(
            f"""
            QWidget#ioDetailedOscilloscopeView {{
                background-color: {palette['background']};
                color: {palette['text']};
            }}
            QPlainTextEdit {{
                background-color: {palette['panel']};
                color: {palette['text']};
                border: 1px solid {palette['grid']};
                border-radius: 6px;
                padding: 8px;
            }}
            QLabel {{
                color: {palette['text']};
            }}
            """
        )
        if PLOT_AVAILABLE:
            self._plotWidget.setBackground(palette["panel"])

    def _render_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._detail_lines = [
            f"UI: {self.title}",
            f"Theme: {snapshot.get('theme_name', 'n/a')} ({snapshot.get('orientation', 'n/a')})",
            f"Source: {snapshot.get('input_source', 'n/a')}",
            f"Session: {snapshot.get('session_mode', 'idle')}",
            f"Running: {snapshot.get('running', False)}",
            f"Scale: {snapshot.get('scale', 1.0):.2f}",
            f"Offset: {snapshot.get('offset', 0.0):.2f}",
            f"Tee: {snapshot.get('tee_output_mode', 'none')}",
            f"Viewport: {snapshot.get('viewport_start', 0)}:{snapshot.get('viewport_window_size', 0)}",
            f"Samples: {snapshot.get('sample_count', len(snapshot['signal']))}",
            f"Bytes read: {snapshot.get('bytes_read', 0)}",
            f"Bytes written: {snapshot.get('bytes_written', 0)}",
            f"Buffer: {snapshot.get('buffer_size', 0)}",
        ]
        if not QT_AVAILABLE:
            return

        self._details.setPlainText("\n".join(self._detail_lines))
        if PLOT_AVAILABLE and self._curve is not None:
            x_axis = list(range(len(snapshot["signal"])))
            self._curve.setData(x_axis, snapshot["signal"])

    def _handle_theme_updated(self) -> None:
        self._apply_stylesheet()
