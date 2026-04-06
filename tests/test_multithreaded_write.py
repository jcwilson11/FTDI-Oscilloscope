import threading
import time
import unittest
from pathlib import Path

from ioLibrary.data_buffer import DataBuffer
from ioLibrary.multithreaded_write import (
    FileByteStream,
    OutputScheduler,
    RecoveryManager,
    ThroughputMonitor,
    TransferConfig,
    UsbWriteController,
)


class FailingOutputStream:
    def __init__(self):
        self.connected = False

    def open(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False

    def write_bytes(self, data: bytes) -> int:
        raise RuntimeError("simulated write error")

    def is_connected(self) -> bool:
        return self.connected


class RecordingOutputStream:
    def __init__(self):
        self.connected = False
        self.close_calls = 0
        self.written = bytearray()

    def open(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False
        self.close_calls += 1

    def write_bytes(self, data: bytes) -> int:
        self.written.extend(data)
        return len(data)

    def is_connected(self) -> bool:
        return self.connected


class PartialOutputStream:
    def __init__(self, max_chunk_size: int):
        self.max_chunk_size = max_chunk_size
        self.connected = False
        self.written = bytearray()

    def open(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False

    def write_bytes(self, data: bytes) -> int:
        chunk = data[: self.max_chunk_size]
        self.written.extend(chunk)
        return len(chunk)

    def is_connected(self) -> bool:
        return self.connected


class TestDataBuffer(unittest.TestCase):
    def test_push_then_pop_preserves_order_with_wraparound(self):
        buffer = DataBuffer(capacity=5)

        buffer.push(b"ABC")
        self.assertEqual(buffer.pop(2), b"AB")
        buffer.push(b"DEF")

        self.assertEqual(buffer.pop(4), b"CDEF")
        self.assertTrue(buffer.is_empty())

    def test_producer_blocks_until_space_is_available(self):
        buffer = DataBuffer(capacity=4)
        finished = threading.Event()

        buffer.push(b"ABCD")

        def producer():
            buffer.push(b"EF")
            finished.set()

        thread = threading.Thread(target=producer)
        thread.start()

        time.sleep(0.1)
        self.assertFalse(finished.is_set())

        self.assertEqual(buffer.pop(4), b"ABCD")
        thread.join(timeout=1.0)
        self.assertTrue(finished.is_set())
        self.assertEqual(buffer.pop(2), b"EF")

    def test_consumer_blocks_until_data_is_available(self):
        buffer = DataBuffer(capacity=4)
        results = []
        finished = threading.Event()

        def consumer():
            results.append(buffer.pop(4))
            finished.set()

        thread = threading.Thread(target=consumer)
        thread.start()

        time.sleep(0.1)
        self.assertFalse(finished.is_set())

        buffer.push(b"WXYZ")
        thread.join(timeout=1.0)
        self.assertTrue(finished.is_set())
        self.assertEqual(results, [b"WXYZ"])

    def test_close_wakes_waiters_and_closed_empty_pop_returns_empty(self):
        buffer = DataBuffer(capacity=4)

        buffer.close()

        self.assertEqual(buffer.pop(4), b"")
        self.assertTrue(buffer.is_closed())

    def test_push_to_closed_buffer_raises(self):
        buffer = DataBuffer(capacity=4)
        buffer.close()

        with self.assertRaises(RuntimeError):
            buffer.push(b"A")

    def test_close_wakes_blocked_producer(self):
        buffer = DataBuffer(capacity=2)
        finished = threading.Event()
        errors = []

        buffer.push(b"AB")

        def producer():
            try:
                buffer.push(b"C")
            except RuntimeError as exc:
                errors.append(str(exc))
            finally:
                finished.set()

        thread = threading.Thread(target=producer)
        thread.start()

        time.sleep(0.1)
        self.assertFalse(finished.is_set())

        buffer.close()
        thread.join(timeout=1.0)

        self.assertTrue(finished.is_set())
        self.assertTrue(any("closed buffer" in message for message in errors))


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
        self.assertEqual(self.output_file.read_bytes(), b"ABCDEFGH")
        self.assertGreater(throughput_monitor.total_written, 0)
        self.assertFalse(recovery_manager.safe_stopped)

    def test_writer_drains_remaining_data_on_stop(self):
        cfg = TransferConfig(output_hz=1000.0, bytes_per_write=2)
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
        writer.stop()

        self.assertEqual(self.output_file.read_bytes(), b"123456")
        self.assertTrue(buffer.is_empty())

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
        time.sleep(0.2)
        writer.stop()

        self.assertFalse(writer.is_running())

    def test_writer_closes_stream_when_worker_loop_exits(self):
        cfg = TransferConfig(output_hz=1000.0, bytes_per_write=4)
        buffer = DataBuffer(capacity=32)
        throughput_monitor = ThroughputMonitor()
        recovery_manager = RecoveryManager()
        scheduler = OutputScheduler()
        stream = RecordingOutputStream()

        writer = UsbWriteController(
            stream=stream,
            cfg=cfg,
            buffer=buffer,
            throughput_monitor=throughput_monitor,
            recovery_manager=recovery_manager,
            scheduler=scheduler,
        )

        buffer.push(b"DATA")
        writer.start()
        time.sleep(0.05)
        buffer.close()
        writer.join(timeout=1.0)

        self.assertEqual(bytes(stream.written), b"DATA")
        self.assertEqual(stream.close_calls, 1)
        self.assertFalse(stream.is_connected())
        self.assertFalse(writer.is_running())

    def test_writer_enters_safe_stop_on_failure(self):
        cfg = TransferConfig(output_hz=10.0, bytes_per_write=4)
        buffer = DataBuffer(capacity=32)
        throughput_monitor = ThroughputMonitor()
        recovery_manager = RecoveryManager()
        scheduler = OutputScheduler()
        stream = FailingOutputStream()

        writer = UsbWriteController(
            stream=stream,
            cfg=cfg,
            buffer=buffer,
            throughput_monitor=throughput_monitor,
            recovery_manager=recovery_manager,
            scheduler=scheduler,
        )

        buffer.push(b"FAIL")
        writer.start()
        time.sleep(0.2)

        self.assertTrue(recovery_manager.safe_stopped)
        self.assertTrue(any("Write failure" in msg for msg in recovery_manager.messages))
        self.assertTrue(buffer.is_closed())

    def test_writer_retries_until_partial_write_chunk_is_fully_flushed(self):
        cfg = TransferConfig(output_hz=1000.0, bytes_per_write=6)
        buffer = DataBuffer(capacity=32)
        throughput_monitor = ThroughputMonitor()
        recovery_manager = RecoveryManager()
        scheduler = OutputScheduler()
        stream = PartialOutputStream(max_chunk_size=2)

        writer = UsbWriteController(
            stream=stream,
            cfg=cfg,
            buffer=buffer,
            throughput_monitor=throughput_monitor,
            recovery_manager=recovery_manager,
            scheduler=scheduler,
        )

        buffer.push(b"ABCDEF")
        writer.start()
        time.sleep(0.05)
        writer.stop()

        self.assertEqual(bytes(stream.written), b"ABCDEF")
        self.assertEqual(throughput_monitor.total_written, 6)
        self.assertFalse(recovery_manager.safe_stopped)


if __name__ == "__main__":
    unittest.main()
