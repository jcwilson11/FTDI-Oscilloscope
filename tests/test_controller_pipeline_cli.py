import io
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import controller
from ioLibrary.multithreaded_read import FtdiByteStream
from ioLibrary.multithreaded_write import FileByteStream
from ioLibrary.pipeline import PipelineController as RealPipelineController


class FakePipelineController:
    def __init__(self, config):
        self.config = config
        self.started = False
        self.stopped = False
        self.snapshots = {
            "output_mode": config.output_mode,
            "bytes_read": 16,
            "bytes_written": 16,
            "read_throughput_kbps": 1.0,
            "write_throughput_kbps": 1.0,
            "buffer_size": 0,
            "buffer_capacity": config.buffer_capacity,
            "buffer_closed": True,
            "reader_running": False,
            "writer_running": False,
            "safe_stopped": False,
            "recovery_messages": [],
        }

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def is_running(self):
        return False

    def status_snapshot(self):
        return dict(self.snapshots)


class ControllerPipelineCliTests(unittest.TestCase):
    def setUp(self):
        self.output_file = Path("cli_pipeline_output.bin")
        if self.output_file.exists():
            self.output_file.unlink()

    def tearDown(self):
        if self.output_file.exists():
            self.output_file.unlink()

    def test_build_pipeline_config_requires_output_path_for_file_mode(self):
        args = SimpleNamespace(
            duration_seconds=1.0,
            input_device_index=0,
            output_mode="file",
            output_path=None,
            output_device_index=None,
            bytes_per_read=8,
            bytes_per_write=8,
            input_hz=10.0,
            output_hz=10.0,
            buffer_capacity=64,
            dll=None,
        )

        with self.assertRaises(ValueError):
            controller.build_pipeline_config(args)

    def test_build_pipeline_config_requires_output_device_for_ftdi_mode(self):
        args = SimpleNamespace(
            duration_seconds=1.0,
            input_device_index=0,
            output_mode="ftdi",
            output_path=None,
            output_device_index=None,
            bytes_per_read=8,
            bytes_per_write=8,
            input_hz=10.0,
            output_hz=10.0,
            buffer_capacity=64,
            dll=None,
        )

        with self.assertRaises(ValueError):
            controller.build_pipeline_config(args)

    def test_pipeline_main_mode_uses_pipeline_controller(self):
        argv = [
            "controller.py",
            "pipeline",
            "--output-mode",
            "file",
            "--output-path",
            "demo_output.bin",
            "--duration-seconds",
            "0.01",
        ]

        with patch("sys.argv", argv), patch.object(controller, "PipelineController", FakePipelineController):
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                return_code = controller.main()

        self.assertEqual(return_code, 0)
        self.assertIn("Pipeline stopped.", stdout.getvalue())

    def test_pipeline_main_returns_130_on_interrupt(self):
        class InterruptingPipeline(FakePipelineController):
            def start(self):
                super().start()
                raise KeyboardInterrupt

        argv = [
            "controller.py",
            "pipeline",
            "--output-mode",
            "file",
            "--output-path",
            "demo_output.bin",
            "--duration-seconds",
            "0.01",
        ]

        with patch("sys.argv", argv), patch.object(controller, "PipelineController", InterruptingPipeline):
            stderr = io.StringIO()
            with patch("sys.stderr", stderr):
                return_code = controller.main()

        self.assertEqual(return_code, 130)
        self.assertIn("Interrupted.", stderr.getvalue())

    def test_pipeline_main_runs_actual_pipeline_with_fake_streams(self):
        class FakeReadSession:
            def __init__(self, payloads):
                self.payloads = list(payloads)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def read_bytes(self, count: int) -> bytes:
                if not self.payloads:
                    return b""
                return self.payloads.pop(0)[:count]

        def build_fake_pipeline(config):
            input_stream = FtdiByteStream(
                session_factory=lambda: FakeReadSession([b"ABCD", b"EFGH", b"IJKL"]),
            )
            output_stream = FileByteStream(str(self.output_file))
            return RealPipelineController(
                config,
                input_stream=input_stream,
                output_stream=output_stream,
            )

        argv = [
            "controller.py",
            "pipeline",
            "--output-mode",
            "file",
            "--output-path",
            str(self.output_file),
            "--bytes-per-read",
            "4",
            "--bytes-per-write",
            "4",
            "--input-hz",
            "100",
            "--output-hz",
            "100",
            "--buffer-capacity",
            "32",
            "--duration-seconds",
            "0.05",
        ]

        with patch("sys.argv", argv), patch.object(controller, "PipelineController", new=build_fake_pipeline):
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                return_code = controller.main()

        self.assertEqual(return_code, 0)
        self.assertTrue(self.output_file.exists())
        self.assertEqual(self.output_file.read_bytes(), b"ABCDEFGHIJKL")
        self.assertIn("Bytes read: 12", stdout.getvalue())
        self.assertIn("Bytes written: 12", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
