import unittest

from oscilloscope import (
    FilterPipeline,
    ISignalFilter,
    OscilloscopeController,
    OscilloscopeModel,
    OscilloscopeView,
    scpOffset,
    scpScale,
)


class OscilloscopeArchitectureTests(unittest.TestCase):
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

    def test_view_renders_signal_without_model_dependency(self):
        view = OscilloscopeView()

        rendered = view.render([1.0, 2.0, 3.0])

        self.assertEqual(rendered["signal"], [1.0, 2.0, 3.0])
        self.assertEqual(view.lastRenderedSignal, [1.0, 2.0, 3.0])

    def test_controller_creates_model_and_view_via_composition(self):
        controller = OscilloscopeController(filters=[scpScale(2.0), scpOffset(1.0)])

        self.assertIsInstance(controller.model, OscilloscopeModel)
        self.assertIsInstance(controller.view, OscilloscopeView)
        self.assertIsInstance(controller.model.pipeline, FilterPipeline)
        self.assertEqual(len(controller.model.pipeline.filters), 2)

    def test_controller_updates_model_then_notifies_view(self):
        controller = OscilloscopeController(filters=[scpScale(2.0), scpOffset(1.0)])

        rendered = controller.handleUserInput([1.0, 2.0])

        self.assertEqual(controller.model.rawSignal, [1.0, 2.0])
        self.assertEqual(controller.model.processedSignal, [3.0, 5.0])
        self.assertEqual(rendered["signal"], [3.0, 5.0])
        self.assertEqual(controller.view.lastRenderedSignal, [3.0, 5.0])


if __name__ == "__main__":
    unittest.main()
