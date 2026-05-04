import unittest
from pathlib import Path
import time

from oscilloscope import (
    FileWaveformSource,
    FilterPipeline,
    GeneratedWaveformSource,
    ISignalFilter,
    OscilloscopeController,
    OscilloscopeModel,
    OscilloscopeView,
    PLOT_AVAILABLE,
    QT_AVAILABLE,
    SignalSource,
    SampleMappingFilterBase,
    ioCompactOscilloscopeView,
    ioControlState,
    ioDetailedOscilloscopeView,
    ioFtdiWaveformSource,
    ioLandscapeTheme,
    ioLiveSampleHistory,
    ioLiveOscilloscopeSession,
    ioOscilloscopeController,
    ioOscilloscopeModel,
    ioOscilloscopeView,
    ioQtScopeWindow,
    ioRenderState,
    ioSignalSource,
    ioViewTheme,
    ioViewportState,
    ioWaveformGenerator,
    scpOffset,
    scpScale,
)


class FakeFtdiReadableStream:
    def __init__(self, device_index: int = 0, dll_path: str | None = None):
        self.device_index = device_index
        self.dll_path = dll_path
        self.opened = False
        self.closed = False

    def open(self) -> None:
        self.opened = True

    def close(self) -> None:
        self.closed = True

    def read_bytes(self, count: int) -> bytes:
        return bytes((index * 32) % 256 for index in range(count))


class FakeLineEdit:
    def __init__(self, text: str = "", focused: bool = False):
        self._text = text
        self._focused = focused

    def hasFocus(self) -> bool:
        return self._focused

    def text(self) -> str:
        return self._text

    def setText(self, value: str) -> None:
        self._text = value


class FakeButton:
    def __init__(self):
        self._style = ""

    def setStyleSheet(self, value: str) -> None:
        self._style = value

    def styleSheet(self) -> str:
        return self._style


class FakeScrollBar:
    def __init__(self):
        self.minimum = 0
        self.maximum = 0
        self.page_step = 0
        self.single_step = 0
        self.value = 0
        self.signals_blocked = False
        self.enabled = True

    def blockSignals(self, blocked: bool) -> None:
        self.signals_blocked = blocked

    def setRange(self, minimum: int, maximum: int) -> None:
        self.minimum = minimum
        self.maximum = maximum

    def setPageStep(self, value: int) -> None:
        self.page_step = value

    def setSingleStep(self, value: int) -> None:
        self.single_step = value

    def setValue(self, value: int) -> None:
        self.value = value

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled


class OscilloscopeArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.input_file = Path("oscilloscope_samples.bin")
        if self.input_file.exists():
            self.input_file.unlink()

    def tearDown(self):
        if self.input_file.exists():
            self.input_file.unlink()

    def test_filters_implement_interface(self):
        self.assertIsInstance(scpScale(2.0), ISignalFilter)
        self.assertIsInstance(scpOffset(1.0), ISignalFilter)

    def test_pipeline_processes_filters_in_order(self):
        pipeline = FilterPipeline([scpScale(2.0), scpOffset(1.0)])
        processed = pipeline.process([1.0, -1.0, 0.5])
        self.assertEqual(processed, [3.0, -1.0, 2.0])

    def test_model_keeps_raw_and_processed_signal_separate(self):
        pipeline = FilterPipeline([scpScale(2.0), scpOffset(0.5)])
        model = OscilloscopeModel(pipeline=pipeline)

        processed = model.setRawSignal([1.0, 2.0])

        self.assertEqual(model.rawSignal, [1.0, 2.0])
        self.assertEqual(processed, [2.5, 4.5])
        self.assertEqual(model.getProcessedSignal(), [2.5, 4.5])

    def test_scale_and_offset_order_independence_uses_same_final_settings(self):
        scale_then_offset = ioOscilloscopeModel()
        offset_then_scale = ioOscilloscopeModel()
        raw_signal = [0.25, -0.5, 1.0]

        scale_then_offset.setRawSignal(raw_signal)
        scale_then_offset.setScale(2.0)
        scale_then_offset.setOffset(0.25)

        offset_then_scale.setRawSignal(raw_signal)
        offset_then_scale.setOffset(0.25)
        offset_then_scale.setScale(2.0)

        self.assertEqual(
            scale_then_offset.getProcessedSignal(),
            offset_then_scale.getProcessedSignal(),
        )

    def test_repeated_runtime_scale_adjustments_recompute_from_raw_signal(self):
        model = ioOscilloscopeModel()
        model.setRawSignal([1.0, -1.0])

        model.setScale(2.0)
        first = model.getProcessedSignal()
        model.setScale(3.0)
        second = model.getProcessedSignal()
        model.setScale(4.0)
        third = model.getProcessedSignal()

        self.assertEqual(first, [2.0, -2.0])
        self.assertEqual(second, [3.0, -3.0])
        self.assertEqual(third, [4.0, -4.0])

    def test_model_scrolls_visible_window_and_clamps(self):
        model = ioOscilloscopeModel(
            viewport_state=ioViewportState(start_index=0, window_size=3),
            control_state=ioControlState(scale=1.0, offset=0.0),
        )
        model.setRawSignal([0, 1, 2, 3, 4, 5])

        self.assertEqual(model.getVisibleSignal(), [0.0, 1.0, 2.0])
        model.scroll(2)
        self.assertEqual(model.getVisibleSignal(), [2.0, 3.0, 4.0])
        model.scroll(99)
        self.assertEqual(model.getVisibleSignal(), [3.0, 4.0, 5.0])

    def test_concrete_views_inherit_from_abstract_view_contract(self):
        compact = ioCompactOscilloscopeView()
        detailed = ioDetailedOscilloscopeView()

        self.assertIsInstance(compact, ioOscilloscopeView)
        self.assertIsInstance(detailed, ioOscilloscopeView)
        self.assertIsInstance(OscilloscopeView(), ioOscilloscopeView)

    def test_compact_view_renders_signal_without_model_dependency(self):
        view = ioCompactOscilloscopeView()
        rendered = view.render([1.0, 2.0, 3.0])

        self.assertEqual(rendered["signal"], [1.0, 2.0, 3.0])
        self.assertEqual(view.lastRenderedSignal, [1.0, 2.0, 3.0])
        self.assertEqual(rendered["view_id"], "compact")

    def test_detailed_view_preserves_render_state_metadata(self):
        view = ioDetailedOscilloscopeView()
        render_state = ioRenderState(
            view_id=view.view_id,
            view_title=view.title,
            canvas=view.canvas,
            controls=view.controls,
            theme_name=view.theme.getName(),
            orientation=view.theme.getOrientation(),
            palette=view.theme.getPalette(),
            input_source="sine",
            scale=1.5,
            offset=0.25,
            sample_time_seconds=0.001,
            sample_duration_seconds=1.0,
            raw_signal=[0.0, 1.0],
            processed_signal=[0.25, 1.75],
            visible_signal=[0.25, 1.75],
            viewport_start=0,
            viewport_window_size=2,
            sample_count=2,
            running=True,
            active_view="detailed",
        )

        rendered = view.render(render_state)

        self.assertEqual(rendered["view_id"], "detailed")
        self.assertEqual(rendered["input_source"], "sine")
        self.assertEqual(view.lastRenderState, render_state)

    def test_controller_creates_model_and_two_distinct_views_via_composition(self):
        controller = OscilloscopeController(filters=[scpScale(2.0), scpOffset(1.0)])

        self.assertIsInstance(controller.model, OscilloscopeModel)
        self.assertIsInstance(controller.views[0], ioCompactOscilloscopeView)
        self.assertIsInstance(controller.views[1], ioDetailedOscilloscopeView)
        self.assertEqual(controller.view.view_id, "compact")

    def test_controller_updates_model_and_fans_out_to_both_views(self):
        controller = ioOscilloscopeController()
        rendered = controller.start([1.0, 2.0, 3.0, 4.0])

        self.assertEqual(controller.model.rawSignal, [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(rendered["view_id"], "compact")
        self.assertEqual(controller.views[0].lastRenderedSignal, controller.views[1].lastRenderedSignal)

    def test_controller_scroll_updates_visible_window_for_views(self):
        controller = ioOscilloscopeController(
            model=ioOscilloscopeModel(viewport_state=ioViewportState(start_index=0, window_size=3))
        )
        controller.start([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])

        rendered = controller.scrollViewport(2)

        self.assertEqual(rendered["signal"], [2.0, 3.0, 4.0])
        self.assertEqual(controller.views[0].lastRenderedSignal, [2.0, 3.0, 4.0])
        self.assertEqual(controller.views[1].lastRenderedSignal, [2.0, 3.0, 4.0])

    def test_controller_can_switch_active_view_without_changing_model_logic(self):
        controller = ioOscilloscopeController()
        controller.start([0.0, 0.5, 1.0])

        rendered = controller.setActiveView("detailed")

        self.assertEqual(controller.view.view_id, "detailed")
        self.assertEqual(rendered["view_id"], "detailed")

    def test_controller_live_session_refreshes_samples_while_running(self):
        controller = ioOscilloscopeController(live_session=ioLiveOscilloscopeSession())

        controller.setInputSource("square")
        controller.start()
        try:
            deadline = time.perf_counter() + 1.0
            while len(controller.model.rawSignal) == 0 and time.perf_counter() < deadline:
                controller.refreshLiveSession()
                time.sleep(0.02)
        finally:
            controller.stop()

        self.assertGreater(len(controller.model.rawSignal), 0)
        self.assertTrue(any(entry["event_type"] == "session_start" for entry in controller.model.eventLog))

    def test_controller_can_enable_and_report_tee_mode(self):
        controller = ioOscilloscopeController()

        controller.setTeeOutputMode("file")
        controller.setTeeOutputEnabled(True)
        snapshot = controller.statusSnapshot()

        self.assertTrue(snapshot["tee_output_enabled"])
        self.assertEqual(snapshot["tee_output_mode"], "file")

    def test_controller_swaps_themes_but_keeps_view_types_fixed(self):
        controller = ioOscilloscopeController()
        controller.start([0.0, 0.5, 1.0])

        controller.setTheme("landscape")

        self.assertEqual(controller.views[0].theme.getName(), "landscape")
        self.assertEqual(controller.views[1].theme.getName(), "portrait")
        self.assertIsInstance(controller.views[0], ioCompactOscilloscopeView)
        self.assertIsInstance(controller.views[1], ioDetailedOscilloscopeView)

    def test_file_backed_refresh_uses_deterministic_input_samples(self):
        self.input_file.write_bytes(b"\x00\x7F\xFF")
        controller = ioOscilloscopeController()
        controller.setInputSource(f"file:{self.input_file}")

        controller.start()

        self.assertEqual(len(controller.model.rawSignal), 3)
        self.assertAlmostEqual(controller.model.rawSignal[0], -1.0)
        self.assertAlmostEqual(controller.model.rawSignal[-1], 1.0)
        self.assertEqual(controller.views[0].lastRenderedSignal, controller.views[1].lastRenderedSignal)
        controller.stop()

    def test_ftdi_waveform_source_normalizes_stream_bytes(self):
        control = ioControlState(
            input_source="ftdi:3",
            ftdi_input_bit_index=5,
            sample_time_seconds=0.001,
            sample_duration_seconds=0.004,
        )
        source = ioFtdiWaveformSource(stream_factory=FakeFtdiReadableStream)

        payload = source.generate(control)

        self.assertEqual(len(payload), 4)
        self.assertAlmostEqual(payload[0], -1.0)
        self.assertAlmostEqual(payload[1], 1.0)
        self.assertAlmostEqual(payload[2], -1.0)
        self.assertAlmostEqual(payload[-1], 1.0)

    def test_live_sample_history_can_track_one_ftdi_bit_as_high_low(self):
        history = ioLiveSampleHistory(bit_index=0)

        history.append_bytes(b"\x00\x01\x00\x01")

        self.assertEqual(history.latest_samples(), [-1.0, 1.0, -1.0, 1.0])

    def test_signal_sources_implement_protocol_and_generator_delegates(self):
        class RejectingSource:
            def supports(self, input_source: str) -> bool:
                return False

            def generate(self, control_state: ioControlState) -> list[float]:
                raise AssertionError("should not be selected")

        class RecordingSource:
            def __init__(self):
                self.calls = 0

            def supports(self, input_source: str) -> bool:
                return input_source == "custom"

            def generate(self, control_state: ioControlState) -> list[float]:
                self.calls += 1
                return [42.0]

        source = RecordingSource()
        generator = ioWaveformGenerator(sources=[RejectingSource(), source])
        control = ioControlState(input_source="custom")

        self.assertIsInstance(GeneratedWaveformSource(), SignalSource)
        self.assertIsInstance(FileWaveformSource(), SignalSource)
        self.assertIsInstance(ioFtdiWaveformSource(stream_factory=FakeFtdiReadableStream), ioSignalSource)
        self.assertEqual(generator.generate(control), [42.0])
        self.assertEqual(source.calls, 1)

    def test_qt_scope_window_tracks_active_view_even_without_qt_dependencies(self):
        compact = ioCompactOscilloscopeView()
        detailed = ioDetailedOscilloscopeView()
        window = ioQtScopeWindow(views=[compact, detailed])
        controller = ioOscilloscopeController(views=[compact, detailed])

        window.connectController(controller)
        window.setActiveView("detailed")

        self.assertEqual(window.activeViewId(), "detailed")
        self.assertIs(window.controller, controller)

    def test_qt_scope_window_does_not_clobber_focused_line_edit_text(self):
        line_edit = FakeLineEdit(text="draft_output.bin", focused=True)

        ioQtScopeWindow._sync_line_edit_text(line_edit, "demo_output.bin")

        self.assertEqual(line_edit.text(), "draft_output.bin")

    def test_qt_scope_window_syncs_unfocused_line_edit_text(self):
        line_edit = FakeLineEdit(text="draft_output.bin", focused=False)

        ioQtScopeWindow._sync_line_edit_text(line_edit, "demo_output.bin")

        self.assertEqual(line_edit.text(), "demo_output.bin")

    def test_qt_scope_window_highlights_last_clicked_transport_button(self):
        window = ioQtScopeWindow(views=[ioCompactOscilloscopeView(), ioDetailedOscilloscopeView()])
        window._startButton = FakeButton()
        window._stopButton = FakeButton()

        window._set_last_transport_action("start")
        self.assertIn("#cfeecf", window._startButton.styleSheet())
        self.assertIn("#d9d9d9", window._stopButton.styleSheet())

        window._set_last_transport_action("stop")
        self.assertIn("#f3caca", window._stopButton.styleSheet())
        self.assertIn("#d9d9d9", window._startButton.styleSheet())

    def test_compact_view_syncs_viewport_scrollbar_from_snapshot(self):
        view = ioCompactOscilloscopeView()
        view._viewportScrollBar = FakeScrollBar()

        view._sync_viewport_scrollbar(
            {
                "sample_count": 250,
                "viewport_window_size": 80,
                "viewport_start": 25,
            }
        )

        self.assertEqual(view._viewportScrollBar.minimum, 0)
        self.assertEqual(view._viewportScrollBar.maximum, 170)
        self.assertEqual(view._viewportScrollBar.page_step, 80)
        self.assertEqual(view._viewportScrollBar.value, 25)

    def test_compact_view_scrollbar_calls_set_viewport_action(self):
        view = ioCompactOscilloscopeView()
        received: list[int] = []

        view.attachActions({"set_viewport": received.append})
        view._handle_viewport_changed(42)

        self.assertEqual(received, [42])

    def test_themes_and_filters_preserve_inheritance_contracts(self):
        self.assertEqual(ioLandscapeTheme.__bases__, (ioViewTheme,))
        self.assertTrue(issubclass(type(scpScale(2.0)), SampleMappingFilterBase))
        self.assertTrue(issubclass(type(scpOffset(1.0)), SampleMappingFilterBase))

    def test_qt_availability_flags_are_explicit_for_environment_sensitive_tests(self):
        self.assertIn(QT_AVAILABLE, (True, False))
        self.assertIn(PLOT_AVAILABLE, (True, False))


if __name__ == "__main__":
    unittest.main()
