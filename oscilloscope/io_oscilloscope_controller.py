from __future__ import annotations

from .io_control_state import ioControlState
from .io_compact_oscilloscope_view import ioCompactOscilloscopeView
from .io_detailed_oscilloscope_view import ioDetailedOscilloscopeView
from .io_filter_pipeline import ioFilterPipeline
from .io_landscape_theme import ioLandscapeTheme
from .io_live_oscilloscope_session import ioLiveOscilloscopeSession
from .io_oscilloscope_model import ioOscilloscopeModel
from .io_oscilloscope_view import ioOscilloscopeView
from .io_portrait_theme import ioPortraitTheme
from .io_render_state import ioRenderState
from .io_signal_filter import ioSignalFilter


class ioOscilloscopeController:
    """Coordinates model updates, acquisition intent, and fan-out to all views."""

    def __init__(
        self,
        *,
        filters: list[ioSignalFilter] | None = None,
        model: ioOscilloscopeModel | None = None,
        views: list[ioOscilloscopeView] | None = None,
        live_session: ioLiveOscilloscopeSession | None = None,
        canvas: str = "Canvas",
        controls: str = "ControlPanel",
    ):
        self.model = model if model is not None else ioOscilloscopeModel()
        if filters is not None:
            self.model.setPipeline(ioFilterPipeline(filters))

        self.views = list(views or self._build_default_views(canvas=canvas, controls=controls))
        self.liveSession = live_session if live_session is not None else ioLiveOscilloscopeSession()
        self.running = False
        self._state_change_listeners: list[callable] = []
        self._seen_recovery_messages = 0
        for view in self.views:
            view.connectController(self)
        self._attach_view_actions()

    @property
    def view(self) -> ioOscilloscopeView:
        active_view_id = self.model.controlState.active_view
        for view in self.views:
            if view.view_id == active_view_id:
                return view
        return self.views[0]

    def start(self, signal: list[float] | None = None) -> dict:
        self.running = True
        if signal is None:
            self.model.refreshSamples()
            self._start_live_session()
        else:
            self.liveSession.stop()
            self.model.setRawSignal(signal)
        self._append_event(
            "session_start",
            {
                "input_source": self.model.controlState.input_source,
                "tee_output_mode": self._effective_tee_mode(),
            },
        )
        return self._render_and_notify()

    def stop(self) -> dict:
        self.liveSession.stop()
        self.running = False
        self._append_event("session_stop", {"input_source": self.model.controlState.input_source})
        return self._render_and_notify()

    def handleUserInput(self, signal: list[float]) -> dict:
        self.model.setRawSignal(signal)
        return self._render_and_notify()

    def setSampleTimeSeconds(self, sample_time_seconds: float) -> dict:
        self.model.setSampleTimeSeconds(sample_time_seconds)
        self._append_event("sample_time_change", {"sample_time_seconds": sample_time_seconds})
        self._restart_live_session_if_running()
        return self.refreshFromControls()

    def setSampleDurationSeconds(self, sample_duration_seconds: float) -> dict:
        self.model.setSampleDurationSeconds(sample_duration_seconds)
        self._append_event("sample_duration_change", {"sample_duration_seconds": sample_duration_seconds})
        return self.refreshFromControls()

    def setInputSource(self, input_source: str) -> dict:
        self.model.setInputSource(input_source)
        self._append_event("source_change", {"input_source": input_source})
        self._restart_live_session_if_running(preview=True)
        return self.refreshFromControls()

    def setScale(self, scale: float) -> dict:
        self.model.setScale(scale)
        self._append_event("scale_change", {"scale": scale})
        return self._render_and_notify()

    def setOffset(self, offset: float) -> dict:
        self.model.setOffset(offset)
        self._append_event("offset_change", {"offset": offset})
        return self._render_and_notify()

    def setTheme(self, theme_name: str) -> dict:
        self.model.setActiveTheme(theme_name)
        self._apply_theme_pair(theme_name)
        self._append_event("theme_change", {"theme": theme_name})
        return self._render_and_notify()

    def setActiveView(self, view_name: str) -> dict:
        self.model.setActiveView(view_name)
        self._append_event("active_view_change", {"active_view": view_name})
        return self._render_and_notify()

    def setFtdiInputDeviceIndex(self, device_index: int) -> dict:
        self.model.setFtdiInputDeviceIndex(device_index)
        self._append_event("ftdi_input_device_change", {"ftdi_input_device_index": device_index})
        self._restart_live_session_if_running(preview=True)
        return self._render_and_notify()

    def setFtdiInputBitIndex(self, bit_index: int) -> dict:
        bit_index = self.model.setFtdiInputBitIndex(bit_index)
        self._append_event("ftdi_input_bit_change", {"ftdi_input_bit_index": bit_index})
        self._restart_live_session_if_running(preview=True)
        return self.refreshFromControls()

    def setFtdiDllPath(self, dll_path: str) -> dict:
        self.model.setFtdiDllPath(dll_path)
        self._append_event("ftdi_dll_path_change", {"ftdi_dll_path": dll_path})
        self._restart_live_session_if_running(preview=True)
        return self._render_and_notify()

    def setGeneratedWaveform(self, waveform: str) -> dict:
        self.model.setGeneratedWaveform(waveform)
        self._append_event("waveform_change", {"generated_waveform": waveform})
        self._restart_live_session_if_running(preview=True)
        return self.refreshFromControls()

    def setLiveFilePath(self, path: str) -> dict:
        self.model.setLiveFilePath(path)
        self._append_event("file_path_change", {"live_file_path": path})
        self._restart_live_session_if_running(preview=True)
        return self.refreshFromControls()

    def setFtdiOutputDeviceIndex(self, device_index: int) -> dict:
        self.model.setFtdiOutputDeviceIndex(device_index)
        self._append_event("ftdi_output_device_change", {"ftdi_output_device_index": device_index})
        self._restart_live_session_if_running()
        return self._render_and_notify()

    def setTeeOutputEnabled(self, enabled: bool) -> dict:
        self.model.setTeeOutputEnabled(enabled)
        self._append_event("tee_output_enabled_change", {"tee_output_enabled": bool(enabled)})
        self._restart_live_session_if_running()
        return self._render_and_notify()

    def setTeeOutputMode(self, mode: str) -> dict:
        self.model.setTeeOutputMode(mode)
        self._append_event("tee_output_mode_change", {"tee_output_mode": mode})
        self._restart_live_session_if_running()
        return self._render_and_notify()

    def setTeeOutputPath(self, path: str) -> dict:
        self.model.setTeeOutputPath(path)
        self._append_event("tee_output_path_change", {"tee_output_path": path})
        self._restart_live_session_if_running()
        return self._render_and_notify()

    def setViewportStart(self, start_index: int) -> dict:
        self.model.setViewportStart(start_index)
        return self._render_and_notify()

    def scrollViewport(self, delta: int) -> dict:
        self.model.scroll(delta)
        return self._render_and_notify()

    def increaseScale(self) -> dict:
        return self.setScale(self.model.controlState.scale + 0.25)

    def decreaseScale(self) -> dict:
        return self.setScale(max(0.25, self.model.controlState.scale - 0.25))

    def increaseOffset(self) -> dict:
        return self.setOffset(self.model.controlState.offset + 0.25)

    def decreaseOffset(self) -> dict:
        return self.setOffset(self.model.controlState.offset - 0.25)

    def refreshFromControls(self) -> dict:
        if self.running:
            return self.refreshLiveSession()
        self.model.refreshSamples()
        return self._render_and_notify()

    def refreshLiveSession(self) -> dict:
        if self.running and self.liveSession is not None:
            window_size = self.model.viewportState.window_size
            history_limit = max(window_size * 8, 2048)
            previous_count = len(self.model.processedSignal)
            previous_start = self.model.viewportState.start_index
            previous_max_start = max(0, previous_count - window_size)
            was_following_tail = previous_start >= previous_max_start

            latest = self.liveSession.latest_samples(history_limit)
            if latest:
                self.model.setRawSignal(latest)
                if was_following_tail:
                    self.model.setViewportStart(max(0, len(self.model.processedSignal) - window_size))
            self._record_recovery_messages()
            if not self.liveSession.is_running() and self.running:
                self.running = False
                self._append_event(
                    "session_stop",
                    {"input_source": self.model.controlState.input_source, "reason": "live_session_completed"},
                )
                self._notify_state_change_listeners()
        return self._render_and_notify(notify=False)

    def addStateChangeListener(self, listener) -> None:
        self._state_change_listeners.append(listener)

    def exportPersistentState(self) -> dict[str, dict]:
        return self.model.exportPersistentState()

    def importPersistentState(self, payload: dict | None) -> dict:
        self.model.importPersistentState(payload)
        active_theme = self.model.controlState.active_theme
        if active_theme in {"portrait", "landscape"}:
            self._apply_theme_pair(active_theme)
        return self._render_and_notify()

    def statusSnapshot(self) -> dict:
        live_status = self.liveSession.status_snapshot()
        return {
            "running": self.running,
            "input_source": self.model.controlState.input_source,
            "generated_waveform": self.model.controlState.generated_waveform,
            "live_file_path": self.model.controlState.live_file_path,
            "sample_time_seconds": self.model.controlState.sample_time_seconds,
            "sample_duration_seconds": self.model.controlState.sample_duration_seconds,
            "scale": self.model.controlState.scale,
            "offset": self.model.controlState.offset,
            "theme": self.model.controlState.active_theme,
            "active_view": self.model.controlState.active_view,
            "sample_count": len(self.model.processedSignal),
            "viewport_start": self.model.viewportState.start_index,
            "viewport_window_size": self.model.viewportState.window_size,
            "view_count": len(self.views),
            "ftdi_input_device_index": self.model.controlState.ftdi_input_device_index,
            "ftdi_input_bit_index": self.model.controlState.ftdi_input_bit_index,
            "ftdi_output_device_index": self.model.controlState.ftdi_output_device_index,
            "tee_output_enabled": self.model.controlState.tee_output_enabled,
            "tee_output_mode": self._effective_tee_mode(),
            "tee_output_path": self.model.controlState.tee_output_path,
            "event_count": len(self.model.eventLog),
            "bytes_read": live_status.get("bytes_read", 0),
            "bytes_written": live_status.get("bytes_written", 0),
            "buffer_size": live_status.get("buffer_size", 0),
            "safe_stopped": live_status.get("safe_stopped", False),
            "recovery_messages": live_status.get("recovery_messages", []),
            "session_mode": self._session_mode_name(),
        }

    def _build_default_views(self, *, canvas: str, controls: str) -> list[ioOscilloscopeView]:
        return [
            ioCompactOscilloscopeView(),
            ioDetailedOscilloscopeView(),
        ]

    def _attach_view_actions(self) -> None:
        actions = {
            "scroll_left": lambda: self.scrollViewport(-20),
            "scroll_right": lambda: self.scrollViewport(20),
            "scale_down": self.decreaseScale,
            "scale_up": self.increaseScale,
            "offset_down": self.decreaseOffset,
            "offset_up": self.increaseOffset,
            "refresh": self.refreshFromControls,
            "set_viewport": self.setViewportStart,
            "set_active_view": self.setActiveView,
            "start": self.start,
            "stop": self.stop,
        }
        for view in self.views:
            view.attachActions(actions)

    def _render_all_views(self) -> list[dict]:
        session_status = self.liveSession.status_snapshot()
        visible_signal = self.model.getVisibleSignal()
        snapshots = []
        for view in self.views:
            render_state = ioRenderState(
                view_id=view.view_id,
                view_title=view.title,
                canvas=view.canvas,
                controls=view.controls,
                theme_name=view.theme.getName(),
                orientation=view.theme.getOrientation(),
                palette=view.theme.getPalette(),
                input_source=self.model.controlState.input_source,
                scale=self.model.controlState.scale,
                offset=self.model.controlState.offset,
                sample_time_seconds=self.model.controlState.sample_time_seconds,
                sample_duration_seconds=self.model.controlState.sample_duration_seconds,
                raw_signal=list(self.model.rawSignal),
                processed_signal=list(self.model.processedSignal),
                visible_signal=visible_signal,
                viewport_start=self.model.viewportState.start_index,
                viewport_window_size=self.model.viewportState.window_size,
                sample_count=len(self.model.processedSignal),
                running=self.running,
                active_view=self.model.controlState.active_view,
                ftdi_input_bit_index=self.model.controlState.ftdi_input_bit_index,
                session_mode=self._session_mode_name(),
                tee_output_mode=self._effective_tee_mode(),
                bytes_read=int(session_status.get("bytes_read", 0)),
                bytes_written=int(session_status.get("bytes_written", 0)),
                buffer_size=int(session_status.get("buffer_size", 0)),
                safe_stopped=bool(session_status.get("safe_stopped", False)),
            )
            snapshots.append(view.render(render_state))
        return snapshots

    def _render_and_notify(self, *, notify: bool = True) -> dict:
        snapshots = self._render_all_views()
        if notify:
            self._notify_state_change_listeners()
        active_view_id = self.model.controlState.active_view
        for snapshot in snapshots:
            if snapshot["view_id"] == active_view_id:
                return snapshot
        return snapshots[0]

    def _apply_theme_pair(self, theme_name: str) -> None:
        if theme_name == "portrait":
            themes = [ioPortraitTheme(), ioLandscapeTheme()]
        elif theme_name == "landscape":
            themes = [ioLandscapeTheme(), ioPortraitTheme()]
        else:
            raise ValueError("theme must be 'portrait' or 'landscape'")

        for view, theme in zip(self.views, themes):
            view.setTheme(theme)

    def _append_event(self, event_type: str, payload: dict | None = None) -> None:
        self.model.appendEvent(event_type, payload)

    def _start_live_session(self) -> None:
        history_size = max(self.model.viewportState.window_size * 8, 2048)
        self.liveSession.start(self.model.controlState, history_size=history_size)
        self._seen_recovery_messages = 0

    def _restart_live_session_if_running(self, *, preview: bool = False) -> None:
        if preview:
            self.model.refreshSamples()
        if not self.running:
            return
        self._start_live_session()

    def _record_recovery_messages(self) -> None:
        status = self.liveSession.status_snapshot()
        messages = status.get("recovery_messages", [])
        if not isinstance(messages, list):
            return

        new_messages = messages[self._seen_recovery_messages :]
        if not new_messages:
            return

        for message in new_messages:
            self._append_event("recovery_message", {"message": message})
        self._seen_recovery_messages = len(messages)
        self._notify_state_change_listeners()

    def _session_mode_name(self) -> str:
        source = self.model.controlState.input_source
        if source.startswith("ftdi"):
            return "ftdi"
        if source.startswith("file:"):
            return "live_file"
        return "generated"

    def _effective_tee_mode(self) -> str:
        if not self.model.controlState.tee_output_enabled:
            return "none"
        return self.model.controlState.tee_output_mode

    def _notify_state_change_listeners(self) -> None:
        persistent_state = self.exportPersistentState()
        for listener in self._state_change_listeners:
            listener(persistent_state)


OscilloscopeController = ioOscilloscopeController
