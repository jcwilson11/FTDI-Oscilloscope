import unittest
from pathlib import Path

from ioLibrary import (
    AbstractFileBackedByteStream,
    AbstractReadableByteStream,
    AbstractSessionBackedByteStream,
    AbstractWritableByteStream,
    ByteCountMonitorBase,
    IoLibraryError,
    RateSchedulerBase,
    StreamLifecycle,
    ThreadedWorkerBase,
    ioAcquisitionMonitor,
    ioBuffer,
    ioFileByteStream,
    ioFileInputByteStream,
    ioFtdiByteStream,
    ioFtdiOutputByteStream,
    ioInputScheduler,
    ioOutputScheduler,
    ioRead,
    ioThroughputMonitor,
    ioUsbReadController,
    ioUsbWriteController,
    ioWrite,
)


class FakeSession:
    def __init__(self, read_payload: bytes = b"\x11\x22"):
        self.read_payload = read_payload
        self.writes = []
        self.entered = False
        self.closed = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc, tb):
        self.closed = True

    def write_bytes(self, data: bytes) -> int:
        self.writes.append(bytes(data))
        return len(data)

    def read_bytes(self, count: int) -> bytes:
        return self.read_payload[:count]


class NonContextReadSession:
    def __init__(self):
        self.opened = False
        self.initialized = False
        self.direction_mask = None
        self.closed = False

    def open(self):
        self.opened = True

    def initialize_bitbang(self, direction_mask: int = 0xFF, usb_buffer_size: int = 64):
        self.initialized = True
        self.direction_mask = direction_mask

    def close(self):
        self.closed = True

    def read_bytes(self, count: int) -> bytes:
        return b"A" * count


class NonContextWriteSession:
    def __init__(self):
        self.opened = False
        self.direction_mask = None
        self.closed = False
        self.writes = []

    def open(self):
        self.opened = True

    def initialize_bitbang(self, direction_mask: int = 0xFF, usb_buffer_size: int = 64):
        self.direction_mask = direction_mask

    def close(self):
        self.closed = True

    def write_bytes(self, data: bytes) -> int:
        self.writes.append(bytes(data))
        return len(data)


class IoLibraryTests(unittest.TestCase):
    def setUp(self):
        self.input_path = Path("io_library_test_input.bin")
        self.output_path = Path("io_library_test_output.bin")
        for path in (self.input_path, self.output_path):
            if path.exists():
                path.unlink()

    def tearDown(self):
        for path in (self.input_path, self.output_path):
            if path.exists():
                path.unlink()

    def test_buffer_exposes_diagram_style_accessors(self):
        buffer = ioBuffer(2, initial_data=[0xAA, 0x55])

        self.assertEqual(buffer.getSize(), 2)
        self.assertEqual(bytes(buffer.getRaw()), b"\xAA\x55")

    def test_buffer_rejects_oversized_writes(self):
        buffer = ioBuffer(2)
        with self.assertRaises(IoLibraryError):
            buffer.write([0x01, 0x02, 0x03])

    def test_writer_rejects_invalid_frequency(self):
        buffer = ioBuffer(2, initial_data=[0xFF, 0x00])
        with self.assertRaises(IoLibraryError):
            ioWrite(buffer, length=2, frequency_hz=0)

    def test_writer_rejects_invalid_length(self):
        buffer = ioBuffer(2, initial_data=[0xFF, 0x00])
        with self.assertRaises(IoLibraryError):
            ioWrite(buffer, length=3, frequency_hz=1)

    def test_writer_uses_external_buffer_contents(self):
        buffer = ioBuffer(2, initial_data=[0xFF, 0x00])
        session = FakeSession()
        writer = ioWrite(buffer, length=2, frequency_hz=10, session_factory=lambda: session)

        written = writer.write_once()

        self.assertEqual(written, 2)
        self.assertEqual(session.writes, [b"\xFF\x00"])
        self.assertTrue(session.entered)
        self.assertTrue(session.closed)

    def test_writer_supports_setter_style_configuration(self):
        buffer = ioBuffer(2, initial_data=[0xFF, 0x00])
        session = FakeSession()
        writer = ioWrite(session_factory=lambda: session)

        writer.setBuffer(buffer).setFrequency(10).setM(2)
        written = writer.executeWrite()

        self.assertEqual(written, 2)
        self.assertEqual(writer.length, 2)
        self.assertEqual(session.writes, [b"\xFF\x00"])

    def test_writer_runs_requested_cycles(self):
        buffer = ioBuffer(2, initial_data=[0xFF, 0x00])
        session = FakeSession()
        writer = ioWrite(buffer, length=2, frequency_hz=1000, session_factory=lambda: session)

        cycles = writer.start(cycles=3)

        self.assertEqual(cycles, 3)
        self.assertEqual(session.writes, [b"\xFF\x00", b"\xFF\x00", b"\xFF\x00"])

    def test_writer_sequence_writes_each_state_separately(self):
        buffer = ioBuffer(2, initial_data=[0xFF, 0x00])
        session = FakeSession()
        writer = ioWrite(buffer, length=2, frequency_hz=1000, session_factory=lambda: session)

        cycles = writer.start_sequence(cycles=2)

        self.assertEqual(cycles, 2)
        self.assertEqual(session.writes, [b"\xFF", b"\x00", b"\xFF", b"\x00"])

    def test_reader_stores_data_in_supplied_buffer(self):
        buffer = ioBuffer(4)
        session = FakeSession(read_payload=b"\xAA\x55")
        reader = ioRead(buffer, byte_count=2, frequency_hz=5, session_factory=lambda: session)

        data = reader.read_once()

        self.assertEqual(data, b"\xAA\x55")
        self.assertEqual(buffer.read(2), b"\xAA\x55")
        self.assertEqual(buffer.to_list(), [0xAA, 0x55, 0x00, 0x00])

    def test_reader_supports_setter_style_configuration(self):
        buffer = ioBuffer(4)
        session = FakeSession(read_payload=b"\x10\x20")
        reader = ioRead(session_factory=lambda: session)

        reader.setBuffer(buffer).setFrequency(5).setN(2)
        data = reader.executeRead()

        self.assertEqual(data, b"\x10\x20")
        self.assertEqual(reader.byte_count, 2)
        self.assertEqual(buffer.read(2), b"\x10\x20")

    def test_stream_contracts_and_bases_are_explicit(self):
        self.assertTrue(issubclass(ioFtdiByteStream, AbstractReadableByteStream))
        self.assertTrue(issubclass(ioFtdiByteStream, AbstractSessionBackedByteStream))
        self.assertTrue(issubclass(ioFtdiOutputByteStream, AbstractWritableByteStream))
        self.assertTrue(issubclass(ioFtdiOutputByteStream, AbstractSessionBackedByteStream))
        self.assertTrue(issubclass(ioFileInputByteStream, AbstractReadableByteStream))
        self.assertTrue(issubclass(ioFileInputByteStream, AbstractFileBackedByteStream))
        self.assertTrue(issubclass(ioFileByteStream, AbstractWritableByteStream))
        self.assertTrue(issubclass(ioFileByteStream, AbstractFileBackedByteStream))
        self.assertIsInstance(ioFileByteStream(str(self.output_path), append=False), StreamLifecycle)

    def test_session_backed_streams_share_open_and_close_lifecycle(self):
        read_session = NonContextReadSession()
        write_session = NonContextWriteSession()
        input_stream = ioFtdiByteStream(session_factory=lambda: read_session)
        output_stream = ioFtdiOutputByteStream(session_factory=lambda: write_session)

        input_stream.open()
        output_stream.open()
        output_stream.write_bytes(b"AB")
        input_stream.close()
        output_stream.close()

        self.assertTrue(read_session.opened)
        self.assertTrue(read_session.initialized)
        self.assertEqual(read_session.direction_mask, 0x00)
        self.assertTrue(read_session.closed)
        self.assertTrue(write_session.opened)
        self.assertEqual(write_session.direction_mask, 0xFF)
        self.assertTrue(write_session.closed)
        self.assertEqual(write_session.writes, [b"AB"])

    def test_file_backed_streams_preserve_exhaustion_and_overwrite_behavior(self):
        self.input_path.write_bytes(b"XYZ")
        input_stream = ioFileInputByteStream(str(self.input_path))
        output_stream = ioFileByteStream(str(self.output_path), append=False)

        input_stream.open()
        output_stream.open()
        payload = input_stream.read_bytes(8)
        trailing = input_stream.read_bytes(8)
        output_stream.write_bytes(payload)
        input_stream.close()
        output_stream.close()

        self.assertEqual(payload, b"XYZ")
        self.assertEqual(trailing, b"")
        self.assertTrue(input_stream.is_exhausted())
        self.assertEqual(self.output_path.read_bytes(), b"XYZ")

    def test_worker_scheduler_and_monitor_classes_share_common_bases(self):
        self.assertTrue(issubclass(ioUsbReadController, ThreadedWorkerBase))
        self.assertTrue(issubclass(ioUsbWriteController, ThreadedWorkerBase))
        self.assertTrue(issubclass(ioInputScheduler, RateSchedulerBase))
        self.assertTrue(issubclass(ioOutputScheduler, RateSchedulerBase))
        self.assertTrue(issubclass(ioAcquisitionMonitor, ByteCountMonitorBase))
        self.assertTrue(issubclass(ioThroughputMonitor, ByteCountMonitorBase))


if __name__ == "__main__":
    unittest.main()
