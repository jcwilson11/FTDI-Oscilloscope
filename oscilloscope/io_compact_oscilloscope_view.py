from __future__ import annotations

from typing import Any

from ._qt_compat import PLOT_AVAILABLE, QT_AVAILABLE, QtCore, QtWidgets, ensure_qt_application, ioQtViewMeta, pg
from .io_oscilloscope_view import ioOscilloscopeView
from .io_portrait_theme import ioPortraitTheme


_QtWidgetBase = QtWidgets.QWidget if QT_AVAILABLE else object


class ioCompactOscilloscopeView(ioOscilloscopeView, _QtWidgetBase, metaclass=ioQtViewMeta):
    """Compact Qt view focused on controls-first oscilloscope interaction."""

    def __init__(self, parent=None):
        if QT_AVAILABLE:
            ensure_qt_application()
            QtWidgets.QWidget.__init__(self, parent)
        ioOscilloscopeView.__init__(
            self,
            view_id="compact",
            title="Compact Oscilloscope UI",
            theme=ioPortraitTheme(),
            canvas="CompactCanvas",
            controls="CompactControls",
        )
        self._status_text = ""

        if QT_AVAILABLE:
            self._statusLabel = QtWidgets.QLabel()
            self._statusLabel.setWordWrap(True)
            self._plotWidget = self._build_plot_widget()
            self._build_layout()

    def _build_plot_widget(self):
        if PLOT_AVAILABLE:
            plot_widget = pg.PlotWidget()
            self._curve = plot_widget.plot(
                pen=pg.mkPen(color=self.theme.getPalette()["signal"], width=2),
                antialias=True,
            )
            plot_widget.showGrid(x=True, y=True, alpha=0.25)
            plot_widget.setMenuEnabled(False)
            plot_widget.setMouseEnabled(x=False, y=False)
            plot_widget.hideButtons()
            plot_widget.setYRange(-5.0, 5.0, padding=0.0)
            plot_widget.enableAutoRange(x=True, y=False)
            return plot_widget

        self._curve = None
        placeholder = QtWidgets.QPlainTextEdit()
        placeholder.setReadOnly(True)
        placeholder.setPlainText("Install pyqtgraph to enable live waveform plotting.")
        return placeholder

    def _build_layout(self) -> None:
        self.setObjectName("ioCompactOscilloscopeView")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        title = QtWidgets.QLabel(self.title)
        title.setObjectName("ioCompactTitle")
        layout.addWidget(title)
        layout.addWidget(self._statusLabel)
        layout.addWidget(self._plotWidget)
        self._apply_stylesheet()

    def _apply_stylesheet(self) -> None:
        if not QT_AVAILABLE:
            return
        palette = self.theme.getPalette()
        self.setStyleSheet(
            f"""
            QWidget#ioCompactOscilloscopeView {{
                background-color: {palette['background']};
                color: {palette['text']};
            }}
            QLabel#ioCompactTitle {{
                font-size: 18px;
                font-weight: 700;
                color: {palette['accent']};
            }}
            QLabel {{
                color: {palette['text']};
            }}
            """
        )
        if PLOT_AVAILABLE:
            self._plotWidget.setBackground(palette["panel"])

    def _render_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._status_text = (
            f"source={snapshot.get('input_source', 'n/a')} "
            f"scale={snapshot.get('scale', 1.0):.2f} "
            f"offset={snapshot.get('offset', 0.0):.2f} "
            f"samples={snapshot.get('sample_count', len(snapshot['signal']))} "
            f"tee={snapshot.get('tee_output_mode', 'none')}"
        )
        if not QT_AVAILABLE:
            return

        self._statusLabel.setText(self._status_text)
        if PLOT_AVAILABLE and self._curve is not None:
            x_axis = list(range(len(snapshot["signal"])))
            self._curve.setData(x_axis, snapshot["signal"])
        else:
            self._plotWidget.setPlainText(self._status_text)

    def _handle_theme_updated(self) -> None:
        self._apply_stylesheet()
