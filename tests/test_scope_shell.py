import io
import json
from unittest.mock import patch
import unittest
from pathlib import Path

from io_scope_shell import ioScopeShell


class ScopeShellTests(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.sample_file = Path("scope_shell_samples.bin")
        self.settings_file = Path("test_io_scope_settings.json")
        if self.sample_file.exists():
            self.sample_file.unlink()
        if self.settings_file.exists():
            self.settings_file.unlink()

    def tearDown(self):
        if self.sample_file.exists():
            self.sample_file.unlink()
        if self.settings_file.exists():
            self.settings_file.unlink()

    def build_shell(self) -> ioScopeShell:
        return ioScopeShell(
            headless=True,
            output_stream=self.output,
            settings_path=self.settings_file,
        )

    def test_shell_updates_control_state_from_professor_commands(self):
        shell = self.build_shell()

        shell.execute("sampleTime=1ms")
        shell.execute("sampleFor=10s")
        shell.execute("input=square")
        shell.execute("scale=2.0")
        shell.execute("offset=0.25")
        shell.execute("theme=landscape")
        message = shell.execute("scope start")
        status = shell.execute("status")

        self.assertIn("Scope started.", message)
        self.assertIn("running=True", status)
        self.assertIn("input=square", status)
        self.assertIn("sampleTime=0.001000s", status)
        self.assertIn("sampleFor=10.000s", status)
        self.assertIn("scale=2.00", status)
        self.assertIn("offset=0.25", status)
        self.assertIn("theme=landscape", status)

    def test_shell_file_input_and_scale_offset_update_both_views(self):
        self.sample_file.write_bytes(b"\x00\x40\x80\xC0\xFF")
        shell = self.build_shell()

        shell.execute(f"input=file:{self.sample_file}")
        shell.execute("scale=1.5")
        shell.execute("offset=0.5")
        shell.execute("scope start")

        controller = shell.controller
        expected = controller.model.getVisibleSignal()
        self.assertEqual(controller.views[0].lastRenderedSignal, expected)
        self.assertEqual(controller.views[1].lastRenderedSignal, expected)
        self.assertAlmostEqual(controller.model.processedSignal[0], -1.0)
        self.assertGreater(controller.model.processedSignal[-1], 1.0)
        shell.execute("stop")

    def test_shell_stop_updates_running_status(self):
        shell = self.build_shell()

        shell.execute("scope start")
        message = shell.execute("stop")
        status = shell.execute("status")

        self.assertIn("Scope stopped.", message)
        self.assertIn("running=False", status)

    def test_shell_loads_defaults_when_settings_file_is_missing(self):
        shell = self.build_shell()

        status = shell.execute("status")

        self.assertIn("input=sine", status)
        self.assertIn("scale=1.00", status)
        self.assertIn("offset=0.00", status)
        self.assertTrue(self.settings_file.exists())

    def test_shell_persists_settings_to_json_and_reloads_them(self):
        first_shell = self.build_shell()
        first_shell.execute("sampleTime=2ms")
        first_shell.execute("sampleFor=5s")
        first_shell.execute("input=triangle")
        first_shell.execute("scale=3.0")
        first_shell.execute("offset=0.5")
        first_shell.execute("theme=landscape")

        payload = json.loads(self.settings_file.read_text(encoding="utf-8"))
        self.assertEqual(payload["control_state"]["input_source"], "triangle")
        self.assertEqual(payload["control_state"]["scale"], 3.0)
        self.assertEqual(payload["control_state"]["offset"], 0.5)
        self.assertTrue(any(entry["event_type"] == "source_change" for entry in payload["event_log"]))

        second_shell = self.build_shell()
        status = second_shell.execute("status")

        self.assertIn("input=triangle", status)
        self.assertIn("sampleTime=0.002000s", status)
        self.assertIn("sampleFor=5.000s", status)
        self.assertIn("scale=3.00", status)
        self.assertIn("offset=0.50", status)
        self.assertIn("theme=landscape", status)

    def test_shell_falls_back_cleanly_when_settings_json_is_malformed(self):
        self.settings_file.write_text("{not valid json", encoding="utf-8")

        shell = self.build_shell()
        status = shell.execute("status")

        self.assertIn("input=sine", status)
        self.assertIn("scale=1.00", status)
        self.assertIn("offset=0.00", status)

    def test_shell_saves_runtime_scale_and_offset_adjustments_without_restart(self):
        shell = self.build_shell()
        shell.execute("scope start")
        shell.execute("scale=2.0")
        shell.execute("scale=3.0")
        shell.execute("offset=0.25")
        shell.execute("scale=4.0")

        payload = json.loads(self.settings_file.read_text(encoding="utf-8"))
        status = shell.execute("status")

        self.assertEqual(payload["control_state"]["scale"], 4.0)
        self.assertEqual(payload["control_state"]["offset"], 0.25)
        self.assertIn("running=True", status)
        self.assertIn("scale=4.00", status)
        self.assertIn("offset=0.25", status)

    def test_shell_writes_event_log_for_start_and_stop(self):
        shell = self.build_shell()

        shell.execute("scope start")
        shell.execute("stop")

        payload = json.loads(self.settings_file.read_text(encoding="utf-8"))
        event_types = [entry["event_type"] for entry in payload["event_log"]]

        self.assertIn("session_start", event_types)
        self.assertIn("session_stop", event_types)

    def test_shell_reports_value_errors_without_crashing(self):
        shell = self.build_shell()

        bad_time = shell.execute("sampleTime=0ms")
        bad_theme = shell.execute("theme=diagonal")

        self.assertIn("Command error:", bad_time)
        self.assertIn("sampleTime must be greater than 0", bad_time)
        self.assertIn("Command error:", bad_theme)
        self.assertIn("theme must be 'portrait' or 'landscape'", bad_theme)

    def test_shell_reports_missing_file_input_without_crashing(self):
        shell = self.build_shell()

        shell.execute("input=file:missing_scope_samples.bin")
        message = shell.execute("scope start")

        self.assertIn("Command error:", message)
        self.assertIn("Input file not found", message)

    def test_headless_shell_does_not_import_tkinter(self):
        original_import = __import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "tkinter":
                raise AssertionError("headless shell should not import tkinter")
            return original_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=guarded_import):
            shell = self.build_shell()

        status = shell.execute("status")
        self.assertIn("views=2", status)


if __name__ == "__main__":
    unittest.main()
