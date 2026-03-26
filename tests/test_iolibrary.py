import unittest

from ioLibrary import IoLibraryError, ioBuffer, ioRead, ioWrite


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


class IoLibraryTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
