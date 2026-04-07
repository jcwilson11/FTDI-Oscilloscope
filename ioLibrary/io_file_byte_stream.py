class ioFileByteStream:
    def __init__(self, output_path: str, *, append: bool = True):
        self.output_path = output_path
        self.append = append
        self.file_handle = None
        self.connected = False

    def open(self) -> None:
        mode = "ab" if self.append else "wb"
        self.file_handle = open(self.output_path, mode)
        self.connected = True

    def close(self) -> None:
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        self.connected = False

    def write_bytes(self, data: bytes) -> int:
        if not self.connected or self.file_handle is None:
            raise RuntimeError("Output stream is not open.")
        self.file_handle.write(data)
        self.file_handle.flush()
        return len(data)

    def is_connected(self) -> bool:
        return self.connected


FileByteStream = ioFileByteStream
