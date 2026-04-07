from .io_library_error import ioLibraryError


class ioFtdiError(ioLibraryError):
    """Raised when the FTDI D2XX layer reports an error."""


FtdiError = ioFtdiError
