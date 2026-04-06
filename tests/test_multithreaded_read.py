import time
import unittest

from ioLibrary.multithreaded_read import (
    AcquisitionConfig,
    AcquisitionMonitor,
    FtdiByteStream,
    InputScheduler,
    UsbReadController,
)
from ioLibrary.multithreaded_write import DataBuffer, RecoveryManager


class FakeReadSession:
    def __init__(self, payloads=None, *, fail_on_read: bool = False):
        self.payloads = list(payloads or [b"ABCD"])
        self.fail_on_read = fail_on_read
        self.entered = False
        self.closed = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc, tb):
        self.closed = True

    def read_bytes(self, count: int) -> bytes:
        if self.fail_on_read:
            raise RuntimeError("simulated read error")
        if not self.payloads:
            return b""
        return self.payloads.pop(0)[:count]


class TestMultithreadedRead(unittest.TestCase):
    def test_reader_moves_data_into_shared_buffer(self):
        cfg = AcquisitionConfig(input_hz=20.0, bytes_per_read=4)
        buffer = DataBuffer(capacity=64)
        acquisition_monitor = AcquisitionMonitor()
        recovery_manager = RecoveryManager()
        scheduler = InputScheduler()
        session = FakeReadSession(payloads=[b"ABCD", b"EFGH"])
        stream = FtdiByteStream(session_factory=lambda: session)

        reader = UsbReadController(
            stream=stream,
            cfg=cfg,
            buffer=buffer,
            acquisition_monitor=acquisition_monitor,
            recovery_manager=recovery_manager,
            scheduler=scheduler,
        )

        reader.start()
        time.sleep(0.2)
        reader.stop()

        self.assertEqual(buffer.pop(8), b"ABCDEFGH")
        self.assertGreaterEqual(acquisition_monitor.total_read, 8)
        self.assertFalse(recovery_manager.safe_stopped)
        self.assertTrue(session.entered)
        self.assertTrue(session.closed)

    def test_reader_stop_leaves_buffer_open_for_pipeline_controller(self):
        cfg = AcquisitionConfig(input_hz=10.0, bytes_per_read=2)
        buffer = DataBuffer(capacity=32)
        acquisition_monitor = AcquisitionMonitor()
        recovery_manager = RecoveryManager()
        scheduler = InputScheduler()
        stream = FtdiByteStream(session_factory=lambda: FakeReadSession(payloads=[b"12"]))

        reader = UsbReadController(
            stream=stream,
            cfg=cfg,
            buffer=buffer,
            acquisition_monitor=acquisition_monitor,
            recovery_manager=recovery_manager,
            scheduler=scheduler,
        )

        reader.start()
        time.sleep(0.1)
        reader.stop()

        self.assertFalse(reader.is_running())
        self.assertFalse(buffer.is_closed())

    def test_reader_enters_safe_stop_on_failure(self):
        cfg = AcquisitionConfig(input_hz=10.0, bytes_per_read=2)
        buffer = DataBuffer(capacity=32)
        acquisition_monitor = AcquisitionMonitor()
        recovery_manager = RecoveryManager()
        scheduler = InputScheduler()
        stream = FtdiByteStream(
            session_factory=lambda: FakeReadSession(fail_on_read=True),
        )

        reader = UsbReadController(
            stream=stream,
            cfg=cfg,
            buffer=buffer,
            acquisition_monitor=acquisition_monitor,
            recovery_manager=recovery_manager,
            scheduler=scheduler,
        )

        reader.start()
        time.sleep(0.1)

        self.assertTrue(recovery_manager.safe_stopped)
        self.assertFalse(reader.is_running())
        self.assertTrue(buffer.is_closed())
        self.assertTrue(any("Read failure" in msg for msg in recovery_manager.messages))


if __name__ == "__main__":
    unittest.main()
