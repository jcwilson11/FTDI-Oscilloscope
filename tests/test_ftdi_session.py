import ctypes
import unittest

from ioLibrary._ftdi_session import FtdiSession


class FakeD2xxLibrary:
    def __init__(self):
        self.purge_calls = 0
        self.read_calls = 0

    def FT_Purge(self, handle, mask):
        self.purge_calls += 1
        return 0

    def FT_Read(self, handle, payload, count, read_ptr):
        self.read_calls += 1
        data = b"ABC"[:count]
        for index, value in enumerate(data):
            payload[index] = value
        ctypes.cast(read_ptr, ctypes.POINTER(ctypes.c_uint32)).contents.value = len(data)
        return 0


class FtdiSessionTests(unittest.TestCase):
    def test_read_bytes_does_not_purge_receive_queue_each_call(self):
        session = FtdiSession.__new__(FtdiSession)
        session._dll = FakeD2xxLibrary()
        session._handle = ctypes.c_void_p(1)

        data = session.read_bytes(8)

        self.assertEqual(data, b"ABC")
        self.assertEqual(session._dll.read_calls, 1)
        self.assertEqual(session._dll.purge_calls, 0)


if __name__ == "__main__":
    unittest.main()
