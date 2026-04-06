import time
import unittest
from pathlib import Path

from ioLibrary.multithreaded_read import FtdiByteStream
from ioLibrary.multithreaded_write import FileByteStream, FtdiOutputByteStream
from ioLibrary.pipeline import PipelineConfig, PipelineController


class FakeReadSession:
    def __init__(self, payloads=None, *, fail_on_read: bool = False):
        self.payloads = list(payloads or [])
        self.fail_on_read = fail_on_read
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.closed = True

    def read_bytes(self, count: int) -> bytes:
        if self.fail_on_read:
            raise RuntimeError("simulated read error")
        if not self.payloads:
            return b""
        return self.payloads.pop(0)[:count]


class FakeWriteSession:
    def __init__(self, *, fail_on_write: bool = False):
        self.fail_on_write = fail_on_write
        self.written = bytearray()
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.closed = True

    def write_bytes(self, data: bytes) -> int:
        if self.fail_on_write:
            raise RuntimeError("simulated write error")
        self.written.extend(data)
        return len(data)


class PipelineControllerTests(unittest.TestCase):
    def setUp(self):
        self.output_file = Path("pipeline_output.bin")
        if self.output_file.exists():
            self.output_file.unlink()

    def tearDown(self):
        if self.output_file.exists():
            self.output_file.unlink()

    def test_pipeline_moves_data_from_fake_ftdi_to_file(self):
        read_session = FakeReadSession(payloads=[b"ABCD", b"EFGH", b"IJKL"])
        input_stream = FtdiByteStream(session_factory=lambda: read_session)
        output_stream = FileByteStream(str(self.output_file))
        cfg = PipelineConfig(
            output_mode="file",
            output_path=str(self.output_file),
            bytes_per_read=4,
            bytes_per_write=4,
            input_hz=100.0,
            output_hz=100.0,
            buffer_capacity=32,
        )

        pipeline = PipelineController(cfg, input_stream=input_stream, output_stream=output_stream)
        pipeline.start()
        time.sleep(0.2)
        pipeline.stop()

        self.assertEqual(self.output_file.read_bytes(), b"ABCDEFGHIJKL")
        self.assertTrue(pipeline.buffer.is_empty())
        self.assertEqual(pipeline.status_snapshot()["bytes_written"], 12)

    def test_pipeline_moves_data_from_fake_ftdi_to_fake_ftdi_sink(self):
        read_session = FakeReadSession(payloads=[b"12", b"34", b"56"])
        write_session = FakeWriteSession()
        input_stream = FtdiByteStream(session_factory=lambda: read_session)
        output_stream = FtdiOutputByteStream(session_factory=lambda: write_session)
        cfg = PipelineConfig(
            output_mode="ftdi",
            output_device_index=1,
            bytes_per_read=2,
            bytes_per_write=2,
            input_hz=100.0,
            output_hz=100.0,
            buffer_capacity=16,
        )

        pipeline = PipelineController(cfg, input_stream=input_stream, output_stream=output_stream)
        pipeline.start()
        time.sleep(0.2)
        pipeline.stop()

        self.assertEqual(bytes(write_session.written), b"123456")
        self.assertTrue(pipeline.buffer.is_empty())
        self.assertEqual(pipeline.status_snapshot()["bytes_read"], 6)

    def test_pipeline_safe_stop_is_reported_on_write_failure(self):
        read_session = FakeReadSession(payloads=[b"FAIL"])
        write_session = FakeWriteSession(fail_on_write=True)
        input_stream = FtdiByteStream(session_factory=lambda: read_session)
        output_stream = FtdiOutputByteStream(session_factory=lambda: write_session)
        cfg = PipelineConfig(
            output_mode="ftdi",
            output_device_index=1,
            bytes_per_read=4,
            bytes_per_write=4,
            input_hz=100.0,
            output_hz=100.0,
            buffer_capacity=16,
        )

        pipeline = PipelineController(cfg, input_stream=input_stream, output_stream=output_stream)
        pipeline.start()
        time.sleep(0.2)
        pipeline.stop()

        snapshot = pipeline.status_snapshot()
        self.assertTrue(snapshot["safe_stopped"])
        self.assertTrue(any("Write failure" in msg for msg in snapshot["recovery_messages"]))


if __name__ == "__main__":
    unittest.main()
