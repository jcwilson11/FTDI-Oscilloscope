"""Backward-compatible adapter over the new ioLibrary FTDI session."""

from ioLibrary._ftdi_session import FtdiSession
from ioLibrary.errors import FtdiError


class FtdiDevice(FtdiSession):
    """Compatibility shim for the older controller prototype."""

    def write_byte(self, value: int) -> int:
        return self.write_bytes(bytes([value & 0xFF]))

    def read_byte(self) -> int:
        data = self.read_bytes(1)
        if len(data) != 1:
            raise FtdiError(f"FT_Read returned {len(data)} bytes instead of 1")
        return data[0]
