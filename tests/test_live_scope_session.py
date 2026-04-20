import time
import unittest
from pathlib import Path

from oscilloscope import ioControlState, ioLiveFileTailByteStream, ioLiveOscilloscopeSession


class LiveScopeSessionTests(unittest.TestCase):
    def setUp(self):
        self.input_file = Path("live_scope_input.bin")
        self.output_file = Path("live_scope_output.bin")
        for path in (self.input_file, self.output_file):
            if path.exists():
                path.unlink()

    def tearDown(self):
        for path in (self.input_file, self.output_file):
            if path.exists():
                path.unlink()

    def test_live_file_tail_stream_reads_appends_and_resets_on_truncation(self):
        stream = ioLiveFileTailByteStream(str(self.input_file))
        stream.open()
        try:
            self.input_file.write_bytes(b"ABC")
            self.assertEqual(stream.read_bytes(8), b"ABC")
            self.assertEqual(stream.read_bytes(8), b"")

            self.input_file.write_bytes(b"XY")
            self.assertEqual(stream.read_bytes(8), b"XY")
        finally:
            stream.close()

    def test_live_session_reads_from_live_file_and_tees_to_output_file(self):
        self.input_file.write_bytes(b"\x00\x40\x80")
        control = ioControlState(
            input_source=f"file:{self.input_file}",
            live_file_path=str(self.input_file),
            sample_time_seconds=0.01,
            ftdi_bytes_per_read=8,
            tee_output_enabled=True,
            tee_output_mode="file",
            tee_output_path=str(self.output_file),
        )
        session = ioLiveOscilloscopeSession()

        session.start(control, history_size=64)
        try:
            deadline = time.perf_counter() + 1.0
            while session.status_snapshot()["bytes_written"] < 3 and time.perf_counter() < deadline:
                time.sleep(0.05)

            self.input_file.write_bytes(b"\x00\x40\x80\xC0\xFF")
            deadline = time.perf_counter() + 1.0
            while session.status_snapshot()["bytes_written"] < 5 and time.perf_counter() < deadline:
                time.sleep(0.05)
        finally:
            session.stop()

        latest = session.latest_samples(8)
        self.assertTrue(latest)
        self.assertEqual(self.output_file.read_bytes(), b"\x00\x40\x80\xC0\xFF")
