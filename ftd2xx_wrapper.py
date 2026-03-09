import ctypes
from ctypes import byref, c_char, c_ubyte, c_uint32, c_void_p
from ctypes.util import find_library
from pathlib import Path


FT_OK = 0
FT_PURGE_RX = 1
FT_PURGE_TX = 2
FT_BITMODE_ASYNC_BITBANG = 0x01

FT_STATUS_NAMES = {
    0: "FT_OK",
    1: "FT_INVALID_HANDLE",
    2: "FT_DEVICE_NOT_FOUND",
    3: "FT_DEVICE_NOT_OPENED",
    4: "FT_IO_ERROR",
    5: "FT_INSUFFICIENT_RESOURCES",
    6: "FT_INVALID_PARAMETER",
    7: "FT_INVALID_BAUD_RATE",
    8: "FT_DEVICE_NOT_OPENED_FOR_ERASE",
    9: "FT_DEVICE_NOT_OPENED_FOR_WRITE",
    10: "FT_FAILED_TO_WRITE_DEVICE",
    11: "FT_EEPROM_READ_FAILED",
    12: "FT_EEPROM_WRITE_FAILED",
    13: "FT_EEPROM_ERASE_FAILED",
    14: "FT_EEPROM_NOT_PRESENT",
    15: "FT_EEPROM_NOT_PROGRAMMED",
    16: "FT_INVALID_ARGS",
    17: "FT_NOT_SUPPORTED",
    18: "FT_OTHER_ERROR",
    19: "FT_DEVICE_LIST_NOT_READY",
}


class FtdiError(RuntimeError):
    pass


class FtdiDevice:
    def __init__(self, dll_path: str | None = None):
        self._dll = self._load_library(dll_path)
        self._handle = c_void_p()
        self._configure_signatures()

    @staticmethod
    def _load_library(dll_path: str | None):
        candidates = []
        if dll_path:
            candidates.append(Path(dll_path))

        repo_candidate = Path(__file__).resolve().parent / "ftd2xx.dll"
        candidates.append(repo_candidate)

        library_name = find_library("ftd2xx")
        if library_name:
            candidates.append(library_name)

        candidates.extend(["ftd2xx.dll", "FTD2XX.dll"])

        last_error = None
        for candidate in candidates:
            try:
                return ctypes.WinDLL(str(candidate))
            except OSError as exc:
                last_error = exc

        raise FtdiError(
            "Could not load ftd2xx.dll. Install the FTDI D2XX driver or place "
            "ftd2xx.dll next to this script."
        ) from last_error

    def _configure_signatures(self):
        self._dll.FT_Open.argtypes = [c_uint32, ctypes.POINTER(c_void_p)]
        self._dll.FT_Open.restype = c_uint32

        self._dll.FT_CreateDeviceInfoList.argtypes = [ctypes.POINTER(c_uint32)]
        self._dll.FT_CreateDeviceInfoList.restype = c_uint32

        self._dll.FT_GetDeviceInfoDetail.argtypes = [
            c_uint32,
            ctypes.POINTER(c_uint32),
            ctypes.POINTER(c_uint32),
            ctypes.POINTER(c_uint32),
            ctypes.POINTER(c_uint32),
            ctypes.POINTER(c_char),
            ctypes.POINTER(c_char),
            ctypes.POINTER(c_void_p),
        ]
        self._dll.FT_GetDeviceInfoDetail.restype = c_uint32

        self._dll.FT_Close.argtypes = [c_void_p]
        self._dll.FT_Close.restype = c_uint32

        self._dll.FT_ResetDevice.argtypes = [c_void_p]
        self._dll.FT_ResetDevice.restype = c_uint32

        self._dll.FT_Purge.argtypes = [c_void_p, c_uint32]
        self._dll.FT_Purge.restype = c_uint32

        self._dll.FT_SetUSBParameters.argtypes = [c_void_p, c_uint32, c_uint32]
        self._dll.FT_SetUSBParameters.restype = c_uint32

        self._dll.FT_SetBitMode.argtypes = [c_void_p, c_ubyte, c_ubyte]
        self._dll.FT_SetBitMode.restype = c_uint32

        self._dll.FT_Write.argtypes = [
            c_void_p,
            ctypes.c_void_p,
            c_uint32,
            ctypes.POINTER(c_uint32),
        ]
        self._dll.FT_Write.restype = c_uint32

        self._dll.FT_Read.argtypes = [
            c_void_p,
            ctypes.c_void_p,
            c_uint32,
            ctypes.POINTER(c_uint32),
        ]
        self._dll.FT_Read.restype = c_uint32

    def _check(self, status: int, function_name: str):
        if status != FT_OK:
            status_name = FT_STATUS_NAMES.get(status, "UNKNOWN_FT_STATUS")
            raise FtdiError(f"{function_name} failed with {status_name} ({status})")

    def open(self, index: int = 0):
        status = self._dll.FT_Open(index, byref(self._handle))
        self._check(status, "FT_Open")

    def initialize_bitbang(self, direction_mask: int = 0xFF, baud_buffer_size: int = 64):
        self._check(self._dll.FT_ResetDevice(self._handle), "FT_ResetDevice")
        self._check(self._dll.FT_Purge(self._handle, FT_PURGE_RX | FT_PURGE_TX), "FT_Purge")
        self._check(
            self._dll.FT_SetUSBParameters(self._handle, baud_buffer_size, 0),
            "FT_SetUSBParameters",
        )
        self._check(
            self._dll.FT_SetBitMode(
                self._handle,
                c_ubyte(direction_mask),
                c_ubyte(FT_BITMODE_ASYNC_BITBANG),
            ),
            "FT_SetBitMode",
        )

    def write_byte(self, value: int) -> int:
        byte_value = c_ubyte(value & 0xFF)
        written = c_uint32()
        self._check(
            self._dll.FT_Write(self._handle, byref(byte_value), 1, byref(written)),
            "FT_Write",
        )
        return written.value

    def read_byte(self) -> int:
        byte_value = c_ubyte()
        read = c_uint32()
        self._check(self._dll.FT_Purge(self._handle, FT_PURGE_RX), "FT_Purge")
        self._check(
            self._dll.FT_Read(self._handle, byref(byte_value), 1, byref(read)),
            "FT_Read",
        )
        if read.value != 1:
            raise FtdiError(f"FT_Read returned {read.value} bytes instead of 1")
        return byte_value.value

    def close(self):
        if self._handle.value:
            self._check(self._dll.FT_Close(self._handle), "FT_Close")
            self._handle = c_void_p()

    def list_devices(self) -> list[dict]:
        count = c_uint32()
        self._check(
            self._dll.FT_CreateDeviceInfoList(byref(count)),
            "FT_CreateDeviceInfoList",
        )

        devices = []
        for index in range(count.value):
            flags = c_uint32()
            device_type = c_uint32()
            device_id = c_uint32()
            location_id = c_uint32()
            serial = ctypes.create_string_buffer(16)
            description = ctypes.create_string_buffer(64)
            handle = c_void_p()

            self._check(
                self._dll.FT_GetDeviceInfoDetail(
                    index,
                    byref(flags),
                    byref(device_type),
                    byref(device_id),
                    byref(location_id),
                    serial,
                    description,
                    byref(handle),
                ),
                "FT_GetDeviceInfoDetail",
            )

            devices.append(
                {
                    "index": index,
                    "flags": flags.value,
                    "type": device_type.value,
                    "id": device_id.value,
                    "location_id": location_id.value,
                    "serial": serial.value.decode(errors="replace"),
                    "description": description.value.decode(errors="replace"),
                    "handle": handle.value,
                }
            )

        return devices

    def __enter__(self):
        self.open()
        self.initialize_bitbang()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
