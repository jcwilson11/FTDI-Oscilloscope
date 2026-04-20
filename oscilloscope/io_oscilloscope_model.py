from __future__ import annotations

from datetime import datetime

from .io_control_state import ioControlState
from .io_filter_pipeline import ioFilterPipeline
from .io_offset_filter import ioOffsetFilter
from .io_scale_filter import ioScaleFilter
from .io_viewport_state import ioViewportState
from .io_waveform_generator import ioWaveformGenerator


class ioOscilloscopeModel:
    """Stores raw signal state, viewport state, and processed signal state."""

    def __init__(
        self,
        *,
        pipeline: ioFilterPipeline | None = None,
        viewport_state: ioViewportState | None = None,
        control_state: ioControlState | None = None,
        waveform_generator: ioWaveformGenerator | None = None,
    ):
        self.rawSignal: list[float] = []
        self.processedSignal: list[float] = []
        self.eventLog: list[dict] = []
        self.viewportState = viewport_state if viewport_state is not None else ioViewportState()
        self.controlState = control_state if control_state is not None else ioControlState()
        self.waveformGenerator = waveform_generator if waveform_generator is not None else ioWaveformGenerator()
        self.pipeline = pipeline if pipeline is not None else ioFilterPipeline()
        self._uses_control_filters = pipeline is None
        if self._uses_control_filters:
            self._rebuild_control_pipeline()

    def setRawSignal(self, signal: list[float]) -> list[float]:
        self.rawSignal = list(signal)
        self.processedSignal = self.pipeline.process(self.rawSignal)
        self._clamp_viewport()
        return list(self.processedSignal)

    def getProcessedSignal(self) -> list[float]:
        return list(self.processedSignal)

    def getVisibleSignal(self) -> list[float]:
        start = self.viewportState.start_index
        end = start + self.viewportState.window_size
        return list(self.processedSignal[start:end])

    def setViewportStart(self, start_index: int) -> int:
        max_start = max(0, len(self.processedSignal) - self.viewportState.window_size)
        self.viewportState.start_index = min(max(start_index, 0), max_start)
        return self.viewportState.start_index

    def scroll(self, delta: int) -> int:
        return self.setViewportStart(self.viewportState.start_index + delta)

    def setWindowSize(self, window_size: int) -> int:
        self.viewportState.window_size = max(10, window_size)
        self._clamp_viewport()
        return self.viewportState.window_size

    def setScale(self, scale: float) -> float:
        self.controlState.scale = scale
        self._enable_control_filters()
        self._rebuild_control_pipeline()
        self.processedSignal = self.pipeline.process(self.rawSignal)
        self._clamp_viewport()
        return self.controlState.scale

    def setOffset(self, offset: float) -> float:
        self.controlState.offset = offset
        self._enable_control_filters()
        self._rebuild_control_pipeline()
        self.processedSignal = self.pipeline.process(self.rawSignal)
        self._clamp_viewport()
        return self.controlState.offset

    def setInputSource(self, input_source: str) -> str:
        self.controlState.input_source = input_source
        if input_source in {"sine", "square", "triangle", "sawtooth"}:
            self.controlState.generated_waveform = input_source
        elif input_source.startswith("file:"):
            self.controlState.live_file_path = input_source[5:] or self.controlState.live_file_path
        elif input_source.startswith("ftdi:"):
            raw_index = input_source.split(":", 1)[1].strip()
            if raw_index:
                self.controlState.ftdi_input_device_index = int(raw_index)
        return input_source

    def setSampleTimeSeconds(self, sample_time_seconds: float) -> float:
        self.controlState.sample_time_seconds = sample_time_seconds
        return sample_time_seconds

    def setSampleDurationSeconds(self, sample_duration_seconds: float) -> float:
        self.controlState.sample_duration_seconds = sample_duration_seconds
        return sample_duration_seconds

    def setActiveTheme(self, theme_name: str) -> str:
        self.controlState.active_theme = theme_name
        return theme_name

    def setActiveView(self, view_name: str) -> str:
        self.controlState.active_view = view_name
        return view_name

    def setFtdiInputDeviceIndex(self, device_index: int) -> int:
        self.controlState.ftdi_input_device_index = device_index
        return device_index

    def setFtdiDllPath(self, dll_path: str) -> str:
        self.controlState.ftdi_dll_path = dll_path
        return dll_path

    def setGeneratedWaveform(self, waveform: str) -> str:
        self.controlState.generated_waveform = waveform
        if self.controlState.input_source in {"sine", "square", "triangle", "sawtooth"}:
            self.controlState.input_source = waveform
        return waveform

    def setLiveFilePath(self, path: str) -> str:
        self.controlState.live_file_path = path
        if self.controlState.input_source.startswith("file:"):
            self.controlState.input_source = f"file:{path}"
        return path

    def setFtdiOutputDeviceIndex(self, device_index: int) -> int:
        self.controlState.ftdi_output_device_index = device_index
        return device_index

    def setTeeOutputEnabled(self, enabled: bool) -> bool:
        self.controlState.tee_output_enabled = bool(enabled)
        self.controlState.write_to_ftdi_enabled = (
            self.controlState.tee_output_enabled and self.controlState.tee_output_mode == "ftdi"
        )
        return self.controlState.tee_output_enabled

    def setTeeOutputMode(self, mode: str) -> str:
        self.controlState.tee_output_mode = mode
        self.controlState.write_to_ftdi_enabled = (
            self.controlState.tee_output_enabled and mode == "ftdi"
        )
        return mode

    def setTeeOutputPath(self, path: str) -> str:
        self.controlState.tee_output_path = path
        return path

    def setRenderIntervalMs(self, interval_ms: int) -> int:
        self.controlState.render_interval_ms = max(10, int(interval_ms))
        return self.controlState.render_interval_ms

    def appendEvent(self, event_type: str, payload: dict | None = None) -> dict:
        entry = {
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "event_type": event_type,
            "payload": dict(payload or {}),
        }
        self.eventLog.append(entry)
        return entry

    def exportPersistentState(self) -> dict[str, dict]:
        return {
            "control_state": self.controlState.to_dict(),
            "viewport_state": self.viewportState.to_dict(),
            "event_log": list(self.eventLog),
        }

    def importPersistentState(self, payload: dict | None) -> None:
        if not isinstance(payload, dict):
            return

        self.controlState = ioControlState.from_dict(payload.get("control_state"))
        self.viewportState = ioViewportState.from_dict(payload.get("viewport_state"))
        event_log = payload.get("event_log")
        self.eventLog = [entry for entry in event_log if isinstance(entry, dict)] if isinstance(event_log, list) else []
        if self._uses_control_filters:
            self._rebuild_control_pipeline()
        self.processedSignal = self.pipeline.process(self.rawSignal)
        self._clamp_viewport()

    def refreshSamples(self) -> list[float]:
        return self.setRawSignal(self.waveformGenerator.generate(self.controlState))

    def setPipeline(self, pipeline: ioFilterPipeline) -> None:
        self.pipeline = pipeline
        self._uses_control_filters = False
        self.processedSignal = self.pipeline.process(self.rawSignal)
        self._clamp_viewport()

    def _enable_control_filters(self) -> None:
        self._uses_control_filters = True

    def _rebuild_control_pipeline(self) -> None:
        self.pipeline.setFilters(
            [
                ioScaleFilter(self.controlState.scale),
                ioOffsetFilter(self.controlState.offset),
            ]
        )

    def _clamp_viewport(self) -> None:
        self.setViewportStart(self.viewportState.start_index)


OscilloscopeModel = ioOscilloscopeModel
