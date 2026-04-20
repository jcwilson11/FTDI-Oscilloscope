from __future__ import annotations

import sys
import threading
from contextlib import suppress
from pathlib import Path

from oscilloscope import (
    ioCompactOscilloscopeView,
    ioDetailedOscilloscopeView,
    ioOscilloscopeController,
    ioScopeSettingsStore,
)
from oscilloscope._qt_compat import QT_AVAILABLE, QtWidgets


class ioScopeShell:
    """Professor-facing shell that drives the MVC oscilloscope demo."""

    def __init__(
        self,
        *,
        controller: ioOscilloscopeController | None = None,
        input_func=input,
        output_stream=None,
        headless: bool = False,
        settings_path: str | Path | None = None,
    ):
        self.input_func = input_func
        self.output_stream = output_stream if output_stream is not None else sys.stdout
        self.headless = headless
        self._closed = threading.Event()
        self._ui_root = None
        self._ui_thread_ident = None
        self._qt_app = None
        self.settings_store = ioScopeSettingsStore(settings_path)

        if controller is None:
            controller = self._build_default_controller()
        self.controller = controller
        self._load_settings()
        self.controller.addStateChangeListener(self._save_settings)
        self._save_settings(self.controller.exportPersistentState())

    def execute(self, command: str) -> str:
        command = command.strip()
        if not command:
            return "No command entered."
        try:
            if command == "scope start":
                snapshot = self.controller.start()
                return self._format_render_message("Scope started.", snapshot)
            if command == "status":
                if self.controller.running:
                    self.controller.refreshLiveSession()
                return self._format_status()
            if command == "stop":
                snapshot = self.controller.stop()
                return self._format_render_message("Scope stopped.", snapshot)
            if command == "exit":
                self._closed.set()
                if self._ui_root is not None:
                    self._ui_root.quit()
                return "Scope shell exiting."

            if command.startswith("sampleTime="):
                value = self._parse_seconds(command.split("=", 1)[1])
                if value <= 0:
                    raise ValueError("sampleTime must be greater than 0")
                snapshot = self.controller.setSampleTimeSeconds(value)
                return self._format_render_message(f"Sample time set to {value:.6f}s.", snapshot)
            if command.startswith("sampleFor="):
                value = self._parse_seconds(command.split("=", 1)[1])
                if value <= 0:
                    raise ValueError("sampleFor must be greater than 0")
                snapshot = self.controller.setSampleDurationSeconds(value)
                return self._format_render_message(f"Sample duration set to {value:.3f}s.", snapshot)
            if command.startswith("input="):
                value = command.split("=", 1)[1]
                snapshot = self.controller.setInputSource(value)
                return self._format_render_message(f"Input source set to {value}.", snapshot)
            if command.startswith("waveform="):
                value = command.split("=", 1)[1]
                snapshot = self.controller.setGeneratedWaveform(value)
                return self._format_render_message(f"Waveform set to {value}.", snapshot)
            if command.startswith("scale="):
                value = float(command.split("=", 1)[1])
                snapshot = self.controller.setScale(value)
                return self._format_render_message(f"Scale set to {value:.2f}.", snapshot)
            if command.startswith("offset="):
                value = float(command.split("=", 1)[1])
                snapshot = self.controller.setOffset(value)
                return self._format_render_message(f"Offset set to {value:.2f}.", snapshot)
            if command.startswith("liveFile="):
                value = command.split("=", 1)[1]
                snapshot = self.controller.setLiveFilePath(value)
                return self._format_render_message(f"Live file set to {value}.", snapshot)
            if command.startswith("ftdiInputIndex="):
                value = int(command.split("=", 1)[1])
                snapshot = self.controller.setFtdiInputDeviceIndex(value)
                return self._format_render_message(f"FTDI input index set to {value}.", snapshot)
            if command.startswith("ftdiOutputIndex="):
                value = int(command.split("=", 1)[1])
                snapshot = self.controller.setFtdiOutputDeviceIndex(value)
                return self._format_render_message(f"FTDI output index set to {value}.", snapshot)
            if command.startswith("teeMode="):
                value = command.split("=", 1)[1]
                if value == "none":
                    self.controller.setTeeOutputEnabled(False)
                else:
                    self.controller.setTeeOutputMode(value)
                    self.controller.setTeeOutputEnabled(True)
                return self._format_render_message(f"Tee mode set to {value}.", self.controller.refreshFromControls())
            if command.startswith("teePath="):
                value = command.split("=", 1)[1]
                snapshot = self.controller.setTeeOutputPath(value)
                return self._format_render_message(f"Tee path set to {value}.", snapshot)
            if command.startswith("theme="):
                value = command.split("=", 1)[1]
                snapshot = self.controller.setTheme(value)
                return self._format_render_message(f"Primary theme set to {value}.", snapshot)
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            return f"Command error: {exc}"

        return (
            "Unsupported command. Use: scope start, sampleTime=..., sampleFor=..., "
            "input=..., waveform=..., liveFile=..., ftdiInputIndex=..., ftdiOutputIndex=..., "
            "scale=..., offset=..., teeMode=none|file|ftdi, teePath=..., "
            "theme=portrait|landscape, status, stop."
        )

    def run_interactive(self) -> int:
        self._write(
            "Scope shell ready. Commands: scope start, sampleTime=1ms, sampleFor=10s, "
            "input=sine|square|triangle|sawtooth|file:<path>|ftdi:<index>, waveform=square, "
            "liveFile=demo_input.bin, ftdiInputIndex=0, ftdiOutputIndex=1, scale=2.0, "
            "offset=0.25, teeMode=none|file|ftdi, teePath=demo_output.bin, "
            "theme=portrait|landscape, status, stop, exit"
        )
        if self._ui_root is None:
            while not self._closed.is_set():
                try:
                    command = self.input_func("> ")
                except EOFError:
                    break
                self._write(self.execute(command))
            return 0

        self._ui_thread_ident = threading.get_ident()
        thread = threading.Thread(target=self._console_loop, daemon=True)
        thread.start()
        self._ui_root.mainloop()
        self._closed.set()
        thread.join(timeout=1.0)
        return 0

    def _build_default_controller(self) -> ioOscilloscopeController:
        self._ensure_qt_application()
        views = [
            ioCompactOscilloscopeView(),
            ioDetailedOscilloscopeView(),
        ]
        return ioOscilloscopeController(views=views)

    def _ensure_qt_application(self) -> None:
        if not QT_AVAILABLE:
            return

        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
        self._qt_app = app

    def _load_settings(self) -> None:
        self.controller.importPersistentState(self.settings_store.load())

    def _save_settings(self, payload: dict[str, dict]) -> None:
        self.settings_store.save(payload)

    def _console_loop(self) -> None:
        while not self._closed.is_set():
            try:
                command = self.input_func("> ")
            except EOFError:
                self._closed.set()
                self._ui_root.after(0, self._ui_root.quit)
                break
            message = self._execute_on_ui_thread(command)
            self._write(message)

    def _execute_on_ui_thread(self, command: str) -> str:
        if threading.get_ident() == self._ui_thread_ident:
            return self.execute(command)

        result = {"message": ""}
        done = threading.Event()

        def callback():
            try:
                result["message"] = self.execute(command)
            except Exception as exc:  # pragma: no cover - defensive shell path
                result["message"] = f"Scope shell error: {exc}"
            finally:
                done.set()

        self._ui_root.after(0, callback)
        done.wait()
        return result["message"]

    def _parse_seconds(self, raw_value: str) -> float:
        value = raw_value.strip().lower()
        if value.endswith("ms"):
            return float(value[:-2]) / 1000.0
        if value.endswith("s"):
            return float(value[:-1])
        return float(value)

    def _format_status(self) -> str:
        snapshot = self.controller.statusSnapshot()
        return (
            f"running={snapshot['running']} input={snapshot['input_source']} "
            f"waveform={snapshot['generated_waveform']} "
            f"sampleTime={snapshot['sample_time_seconds']:.6f}s "
            f"sampleFor={snapshot['sample_duration_seconds']:.3f}s "
            f"scale={snapshot['scale']:.2f} offset={snapshot['offset']:.2f} "
            f"theme={snapshot['theme']} activeView={snapshot['active_view']} views={snapshot['view_count']} "
            f"samples={snapshot['sample_count']} "
            f"tee={snapshot['tee_output_mode']} "
            f"events={snapshot['event_count']} "
            f"viewport={snapshot['viewport_start']}:{snapshot['viewport_window_size']}"
        )

    def _format_render_message(self, prefix: str, snapshot: dict) -> str:
        return (
            f"{prefix} visible={len(snapshot['signal'])} "
            f"sample_count={snapshot.get('sample_count', len(snapshot['signal']))} "
            f"theme={snapshot.get('theme_name', 'n/a')}"
        )

    def _write(self, message: str) -> None:
        self.output_stream.write(message + "\n")
        with suppress(Exception):
            self.output_stream.flush()
