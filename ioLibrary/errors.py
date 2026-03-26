class IoLibraryError(RuntimeError):
    """Base error for ioLibrary."""


class FtdiError(IoLibraryError):
    """Raised when the FTDI D2XX layer reports an error."""
