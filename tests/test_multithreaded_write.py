import time
import unittest
from pathlib import Path

from ioLibrary.multithreaded_write import (
    TransferConfig,
    ThroughputMonitor,
    RecoveryManager,
    OutputScheduler,
    DataBuffer,
    FileByteStream,
    UsbWriteController,
)


class TestMultithreadedWrite(unittest.TestCase):

    def setUp(self):
        self.output_file = Path("test_output.bin")
        if self.output_file.exists():
            self.output_file.unlink()

    def tearDown(self):
        if self.output_file.exists():
            self.output_file.unlink()

    def test_writer_writes_data_to_file(self):
        cfg = TransferConfig(output_hz=20.0, bytes_per_write=4)
        buffer = DataBuffer(capacity=64)
        throughput_monitor = ThroughputMonitor()
        recovery_manager = RecoveryManager()
        scheduler = OutputScheduler()
        stream = FileByteStream(str(self.output_file))

        writer = UsbWriteController(
            stream=stream,
            cfg=cfg,
            buffer=buffer,
            throughput_monitor=throughput_monitor,
            recovery_manager=recovery_manager,
            scheduler=scheduler,
        )

        buffer.push(b"ABCDEFGH")
        writer.start()
        time.sleep(1.0)
        writer.stop()

        self.assertTrue(self.output_file.exists())

        data = self.output_file.read_bytes()
        self.assertEqual(data, b"ABCDEFGH")
        self.assertGreater(throughput_monitor.total_written, 0)
        self.assertFalse(recovery_manager.safe_stopped)

    def test_writer_stops_cleanly(self):
        cfg = TransferConfig(output_hz=10.0, bytes_per_write=2)
        buffer = DataBuffer(capacity=32)
        throughput_monitor = ThroughputMonitor()
        recovery_manager = RecoveryManager()
        scheduler = OutputScheduler()
        stream = FileByteStream(str(self.output_file))

        writer = UsbWriteController(
            stream=stream,
            cfg=cfg,
            buffer=buffer,
            throughput_monitor=throughput_monitor,
            recovery_manager=recovery_manager,
            scheduler=scheduler,
        )

        buffer.push(b"123456")
        writer.start()
        time.sleep(0.5)
        writer.stop()

        self.assertFalse(writer.is_running())


if __name__ == "__main__":
    unittest.main()