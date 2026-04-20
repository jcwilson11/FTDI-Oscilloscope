import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import controller
from io_scope_qt import run_scope_qt


class ScopeQtTests(unittest.TestCase):
    def setUp(self):
        self.settings_file = Path("test_io_scope_qt_settings.json")
        if self.settings_file.exists():
            self.settings_file.unlink()

    def tearDown(self):
        if self.settings_file.exists():
            self.settings_file.unlink()

    def test_headless_qt_launcher_builds_architecture_without_visual_window(self):
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            return_code = run_scope_qt(headless=True, settings_path=self.settings_file)

        self.assertEqual(return_code, 0)
        self.assertIn("Qt scope window initialized in headless mode", stdout.getvalue())
        self.assertTrue(self.settings_file.exists())

    def test_headless_qt_launcher_persists_existing_settings(self):
        payload = {
            "control_state": {
                "scale": 2.5,
                "offset": 0.75,
                "active_view": "detailed",
                "input_source": "triangle",
            },
            "viewport_state": {
                "start_index": 10,
                "window_size": 123,
            },
            "event_log": [{"event_type": "manual_seed"}],
        }
        self.settings_file.write_text(json.dumps(payload), encoding="utf-8")

        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            return_code = run_scope_qt(headless=True, settings_path=self.settings_file)

        self.assertEqual(return_code, 0)
        stored = json.loads(self.settings_file.read_text(encoding="utf-8"))
        self.assertEqual(stored["control_state"]["scale"], 2.5)
        self.assertEqual(stored["control_state"]["offset"], 0.75)
        self.assertEqual(stored["control_state"]["active_view"], "detailed")
        self.assertEqual(stored["control_state"]["input_source"], "triangle")
        self.assertEqual(stored["viewport_state"]["start_index"], 0)
        self.assertEqual(stored["viewport_state"]["window_size"], 123)
        self.assertEqual(stored["event_log"], [{"event_type": "manual_seed"}])

    def test_controller_main_routes_scope_qt_headless_command(self):
        argv = ["controller.py", "scope-qt", "--headless"]
        with patch("sys.argv", argv):
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                return_code = controller.main()

        self.assertEqual(return_code, 0)
        self.assertIn("active view", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
