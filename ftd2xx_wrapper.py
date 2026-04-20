"""Canonical FTDI adapter plus a backward-compatible legacy alias."""

from ioLibrary._ftdi_session import FtdiSession
from ioLibrary.errors import FtdiError


class ioFtdiDevice(FtdiSession):
    """Canonical FTDI adapter used by professor-facing entrypoints."""

    def write_byte(self, value: int) -> int:
        return self.write_bytes(bytes([value & 0xFF]))

    def read_byte(self) -> int:
        data = self.read_bytes(1)
        if len(data) != 1:
            raise FtdiError(f"FT_Read returned {len(data)} bytes instead of 1")
        return data[0]


# Preserve the older import surface while the canonical class name follows the
# assignment's io<ClassName> convention.
FtdiDevice = ioFtdiDevice
