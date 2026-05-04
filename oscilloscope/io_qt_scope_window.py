from __future__ import annotations

from collections.abc import Iterable

from ._qt_compat import QT_AVAILABLE, QtCore, QtWidgets, ensure_qt_application
from .io_compact_oscilloscope_view import ioCompactOscilloscopeView
from .io_detailed_oscilloscope_view import ioDetailedOscilloscopeView
from .io_oscilloscope_view import ioOscilloscopeView


_QtMainWindowBase = QtWidgets.QMainWindow if QT_AVAILABLE else object


class ioQtScopeWindow(_QtMainWindowBase):
    """Top-level Qt shell that hosts selectable oscilloscope views and live controls."""

    _TRANSPORT_BUTTON_STYLES = {
        "inactive": (
            "QPushButton {"
            " background-color: #d9d9d9;"
            " color: #202020;"
            " font-weight: 600;"
            " border: 1px solid #7f7f7f;"
            " border-radius: 4px;"
            " padding: 6px 14px;"
            "}"
        ),
        "start": (
            "QPushButton {"
            " background-color: #cfeecf;"
            " color: #14361a;"
            " font-weight: 700;"
            " border: 2px solid #2f7d32;"
            " border-radius: 4px;"
            " padding: 6px 14px;"
            "}"
        ),
        "stop": (
            "QPushButton {"
            " background-color: #f3caca;"
            " color: #4d1717;"
            " font-weight: 700;"
            " border: 2px solid #a33a3a;"
            " border-radius: 4px;"
            " padding: 6px 14px;"
            "}"
        ),
    }

    def __init__(
        self,
        *,
        views: Iterable[ioOscilloscopeView] | None = None,
        title: str = "FTDI Oscilloscope",
    ):
        if QT_AVAILABLE:
            ensure_qt_application()
            QtWidgets.QMainWindow.__init__(self)
        self.views = list(views or [ioCompactOscilloscopeView(), ioDetailedOscilloscopeView()])
        self.controller = None
        self._active_view_id = self.views[0].view_id if self.views else "compact"
        self._last_transport_action: str | None = None

        if QT_AVAILABLE:
            self._stack = QtWidgets.QStackedWidget()
            self._viewSelector = QtWidgets.QComboBox()
            self._sourceSelector = QtWidgets.QComboBox()
            self._waveformSelector = QtWidgets.QComboBox()
            self._ftdiInputSpin = QtWidgets.QSpinBox()
            self._liveFileEdit = QtWidgets.QLineEdit()
            self._scaleSpin = QtWidgets.QDoubleSpinBox()
            self._offsetSpin = QtWidgets.QDoubleSpinBox()
            self._startButton = QtWidgets.QPushButton("Start")
            self._stopButton = QtWidgets.QPushButton("Stop")
            self._teeEnabledCheck = QtWidgets.QCheckBox("Enable tee output")
            self._teeOutputSelector = QtWidgets.QComboBox()
            self._teePathEdit = QtWidgets.QLineEdit()
            self._ftdiOutputSpin = QtWidgets.QSpinBox()
            self._statusLabel = QtWidgets.QLabel()
            self._refreshTimer = QtCore.QTimer(self)
            self._build_ui(title)
        else:
            self._status_message = ""

    def _build_ui(self, title: str) -> None:
        for view in self.views:
            self._stack.addWidget(view)
            self._viewSelector.addItem(view.title, view.view_id)

        self._sourceSelector.addItems(["Generated", "FTDI Device", "Live File"])
        self._waveformSelector.addItems(["sine", "square", "triangle", "sawtooth"])
        self._teeOutputSelector.addItems(["None", "File", "FTDI"])

        self._ftdiInputSpin.setRange(0, 255)
        self._ftdiOutputSpin.setRange(0, 255)
        self._scaleSpin.setRange(0.25, 20.0)
        self._scaleSpin.setSingleStep(0.25)
        self._offsetSpin.setRange(-10.0, 10.0)
        self._offsetSpin.setSingleStep(0.25)
        self._statusLabel.setWordWrap(True)

        self._viewSelector.currentIndexChanged.connect(self._handle_view_changed)
        self._sourceSelector.currentTextChanged.connect(self._handle_source_changed)
        self._waveformSelector.currentTextChanged.connect(self._handle_waveform_changed)
        self._ftdiInputSpin.valueChanged.connect(self._handle_ftdi_input_changed)
        self._liveFileEdit.editingFinished.connect(self._handle_live_file_changed)
        self._scaleSpin.valueChanged.connect(self._handle_scale_changed)
        self._offsetSpin.valueChanged.connect(self._handle_offset_changed)
        self._startButton.clicked.connect(self._handle_start_clicked)
        self._stopButton.clicked.connect(self._handle_stop_clicked)
        self._teeEnabledCheck.toggled.connect(self._handle_tee_enabled_changed)
        self._teeOutputSelector.currentTextChanged.connect(self._handle_tee_mode_changed)
        self._teePathEdit.editingFinished.connect(self._handle_tee_path_changed)
        self._ftdiOutputSpin.valueChanged.connect(self._handle_ftdi_output_changed)

        self._refreshTimer.timeout.connect(self._refresh_live)
        self._refreshTimer.setInterval(50)

        controls = QtWidgets.QGridLayout()
        controls.setHorizontalSpacing(10)
        controls.setVerticalSpacing(6)

        controls.addWidget(QtWidgets.QLabel("View"), 0, 0)
        controls.addWidget(self._viewSelector, 0, 1)
        controls.addWidget(QtWidgets.QLabel("Source"), 0, 2)
        controls.addWidget(self._sourceSelector, 0, 3)
        controls.addWidget(QtWidgets.QLabel("Waveform"), 0, 4)
        controls.addWidget(self._waveformSelector, 0, 5)
        controls.addWidget(QtWidgets.QLabel("FTDI In"), 0, 6)
        controls.addWidget(self._ftdiInputSpin, 0, 7)

        controls.addWidget(QtWidgets.QLabel("Live File"), 1, 0)
        controls.addWidget(self._liveFileEdit, 1, 1, 1, 3)
        controls.addWidget(QtWidgets.QLabel("Scale"), 1, 4)
        controls.addWidget(self._scaleSpin, 1, 5)
        controls.addWidget(QtWidgets.QLabel("Offset"), 1, 6)
        controls.addWidget(self._offsetSpin, 1, 7)

        controls.addWidget(self._startButton, 2, 0)
        controls.addWidget(self._stopButton, 2, 1)
        controls.addWidget(self._teeEnabledCheck, 2, 2, 1, 2)
        controls.addWidget(QtWidgets.QLabel("Tee Mode"), 2, 4)
        controls.addWidget(self._teeOutputSelector, 2, 5)
        controls.addWidget(QtWidgets.QLabel("FTDI Out"), 2, 6)
        controls.addWidget(self._ftdiOutputSpin, 2, 7)

        controls.addWidget(QtWidgets.QLabel("Tee Path"), 3, 0)
        controls.addWidget(self._teePathEdit, 3, 1, 1, 7)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addLayout(controls)
        layout.addWidget(self._statusLabel)
        layout.addWidget(self._stack)

        self.setCentralWidget(container)
        self.setWindowTitle(title)
        self.resize(1440, 900)
        self._apply_transport_button_styles()

    def connectController(self, controller) -> None:
        self.controller = controller
        for view in self.views:
            view.connectController(controller)

        if QT_AVAILABLE:
            self._refreshTimer.start()
            self._invoke_controller("refreshFromControls")
            self._sync_controls_from_controller()

    def setActiveView(self, view_id: str) -> None:
        self._active_view_id = view_id
        if QT_AVAILABLE:
            for index, view in enumerate(self.views):
                if view.view_id == view_id:
                    self._stack.setCurrentIndex(index)
                    self._viewSelector.blockSignals(True)
                    self._viewSelector.setCurrentIndex(index)
                    self._viewSelector.blockSignals(False)
                    break

    def activeViewId(self) -> str:
        return self._active_view_id

    def updateStatus(self, message: str) -> None:
        if QT_AVAILABLE:
            self._statusLabel.setText(message)
        else:
            self._status_message = message

    def _handle_view_changed(self, index: int) -> None:
        if index < 0 or index >= len(self.views):
            return
        view = self.views[index]
        self.setActiveView(view.view_id)
        self._invoke_controller("setActiveView", view.view_id)

    def _handle_source_changed(self, label: str) -> None:
        if self.controller is None:
            return

        if label == "Generated":
            input_source = self._waveformSelector.currentText() or "sine"
        elif label == "FTDI Device":
            input_source = f"ftdi:{self._ftdiInputSpin.value()}"
        else:
            input_source = f"file:{self._liveFileEdit.text().strip() or 'demo_input.bin'}"

        self._invoke_controller("setInputSource", input_source)
        self._sync_controls_from_controller()

    def _handle_waveform_changed(self, waveform: str) -> None:
        self._invoke_controller("setGeneratedWaveform", waveform)
        if self._sourceSelector.currentText() == "Generated":
            self._invoke_controller("setInputSource", waveform)
        self._sync_controls_from_controller()

    def _handle_ftdi_input_changed(self, value: int) -> None:
        self._invoke_controller("setFtdiInputDeviceIndex", value)
        if self._sourceSelector.currentText() == "FTDI Device":
            self._invoke_controller("setInputSource", f"ftdi:{value}")
        self._sync_controls_from_controller()

    def _handle_live_file_changed(self) -> None:
        path = self._liveFileEdit.text().strip() or "demo_input.bin"
        self._invoke_controller("setLiveFilePath", path)
        if self._sourceSelector.currentText() == "Live File":
            self._invoke_controller("setInputSource", f"file:{path}")
        self._sync_controls_from_controller()

    def _handle_scale_changed(self, value: float) -> None:
        self._invoke_controller("setScale", value)

    def _handle_offset_changed(self, value: float) -> None:
        self._invoke_controller("setOffset", value)

    def _handle_start_clicked(self) -> None:
        self._set_last_transport_action("start")
        self._invoke_controller("start")

    def _handle_stop_clicked(self) -> None:
        self._set_last_transport_action("stop")
        self._invoke_controller("stop")

    def _handle_tee_enabled_changed(self, enabled: bool) -> None:
        self._invoke_controller("setTeeOutputEnabled", enabled)
        self._sync_controls_from_controller()

    def _handle_tee_mode_changed(self, label: str) -> None:
        mapping = {"None": "none", "File": "file", "FTDI": "ftdi"}
        mode = mapping.get(label, "none")
        self._invoke_controller("setTeeOutputMode", mode)
        if mode == "none":
            self._invoke_controller("setTeeOutputEnabled", False)
        self._sync_controls_from_controller()

    def _handle_tee_path_changed(self) -> None:
        self._invoke_controller("setTeeOutputPath", self._teePathEdit.text().strip() or "demo_output.bin")

    def _handle_ftdi_output_changed(self, value: int) -> None:
        self._invoke_controller("setFtdiOutputDeviceIndex", value)

    def _refresh_live(self) -> None:
        if self.controller is None:
            return
        self._invoke_controller("refreshLiveSession", sync=False)
        self._sync_controls_from_controller()

    def _invoke_controller(self, method_name: str, *args, sync: bool = True) -> None:
        if self.controller is None or not hasattr(self.controller, method_name):
            return

        try:
            getattr(self.controller, method_name)(*args)
        except Exception as exc:  # pragma: no cover - GUI safety path
            self.updateStatus(f"{method_name} failed: {exc}")
            if hasattr(self.controller, "_append_event"):
                self.controller._append_event("recovery_message", {"message": str(exc)})
            if sync:
                self._sync_controls_from_controller()
            return

        if sync:
            self._sync_controls_from_controller()

    def _sync_controls_from_controller(self) -> None:
        if not QT_AVAILABLE or self.controller is None:
            return

        snapshot = self.controller.statusSnapshot()
        control_state = self.controller.model.controlState

        source_label = self._source_label_for_input(control_state.input_source)
        tee_label = self._tee_label_for_mode(snapshot.get("tee_output_mode", "none"))

        for widget in [
            self._viewSelector,
            self._sourceSelector,
            self._waveformSelector,
            self._ftdiInputSpin,
            self._liveFileEdit,
            self._scaleSpin,
            self._offsetSpin,
            self._teeEnabledCheck,
            self._teeOutputSelector,
            self._teePathEdit,
            self._ftdiOutputSpin,
        ]:
            widget.blockSignals(True)

        self.setActiveView(control_state.active_view)
        self._sourceSelector.setCurrentText(source_label)
        self._waveformSelector.setCurrentText(control_state.generated_waveform)
        self._ftdiInputSpin.setValue(control_state.ftdi_input_device_index)
        self._sync_line_edit_text(self._liveFileEdit, control_state.live_file_path)
        self._scaleSpin.setValue(control_state.scale)
        self._offsetSpin.setValue(control_state.offset)
        self._teeEnabledCheck.setChecked(control_state.tee_output_enabled)
        self._teeOutputSelector.setCurrentText(tee_label)
        self._sync_line_edit_text(self._teePathEdit, control_state.tee_output_path)
        self._ftdiOutputSpin.setValue(control_state.ftdi_output_device_index)

        for widget in [
            self._viewSelector,
            self._sourceSelector,
            self._waveformSelector,
            self._ftdiInputSpin,
            self._liveFileEdit,
            self._scaleSpin,
            self._offsetSpin,
            self._teeEnabledCheck,
            self._teeOutputSelector,
            self._teePathEdit,
            self._ftdiOutputSpin,
        ]:
            widget.blockSignals(False)

        self._refreshTimer.setInterval(max(10, control_state.render_interval_ms))
        self._update_control_visibility(source_label, tee_label, control_state.tee_output_enabled)
        self.updateStatus(self._format_status(snapshot))

    def _update_control_visibility(self, source_label: str, tee_label: str, tee_enabled: bool) -> None:
        self._waveformSelector.setEnabled(source_label == "Generated")
        self._ftdiInputSpin.setEnabled(source_label == "FTDI Device")
        self._liveFileEdit.setEnabled(source_label == "Live File")
        self._teeOutputSelector.setEnabled(True)
        self._teePathEdit.setEnabled(tee_enabled and tee_label == "File")
        self._ftdiOutputSpin.setEnabled(tee_enabled and tee_label == "FTDI")

    def _set_last_transport_action(self, action: str | None) -> None:
        self._last_transport_action = action
        self._apply_transport_button_styles()

    def _apply_transport_button_styles(self) -> None:
        if not hasattr(self, "_startButton") or not hasattr(self, "_stopButton"):
            return

        self._startButton.setStyleSheet(self._transport_button_style("start"))
        self._stopButton.setStyleSheet(self._transport_button_style("stop"))

    def _transport_button_style(self, button_name: str) -> str:
        active_style = self._TRANSPORT_BUTTON_STYLES.get(button_name)
        if self._last_transport_action == button_name and active_style is not None:
            return active_style
        return self._TRANSPORT_BUTTON_STYLES["inactive"]

    @staticmethod
    def _sync_line_edit_text(line_edit, value: str) -> None:
        # Preserve in-progress edits while the periodic controller sync is running.
        if line_edit.hasFocus():
            return
        if line_edit.text() != value:
            line_edit.setText(value)

    def _source_label_for_input(self, input_source: str) -> str:
        if input_source.startswith("ftdi"):
            return "FTDI Device"
        if input_source.startswith("file:"):
            return "Live File"
        return "Generated"

    def _tee_label_for_mode(self, mode: str) -> str:
        mapping = {"none": "None", "file": "File", "ftdi": "FTDI"}
        return mapping.get(mode, "None")

    def _format_status(self, snapshot: dict) -> str:
        return (
            f"running={snapshot.get('running', False)} "
            f"source={snapshot.get('input_source', 'n/a')} "
            f"samples={snapshot.get('sample_count', 0)} "
            f"bytes_read={snapshot.get('bytes_read', 0)} "
            f"bytes_written={snapshot.get('bytes_written', 0)} "
            f"buffer={snapshot.get('buffer_size', 0)} "
            f"tee={snapshot.get('tee_output_mode', 'none')} "
            f"events={snapshot.get('event_count', 0)}"
        )
