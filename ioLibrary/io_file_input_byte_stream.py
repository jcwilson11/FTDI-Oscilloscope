class ioFileInputByteStream:
    def __init__(self, input_path: str):
        self.input_path = input_path
        self.file_handle = None
        self.connected = False
        self.exhausted = False

    def open(self) -> None:
        self.file_handle = open(self.input_path, "rb")
        self.connected = True
        self.exhausted = False

    def close(self) -> None:
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        self.connected = False

    def read_bytes(self, count: int) -> bytes:
        if not self.connected or self.file_handle is None:
            raise RuntimeError("Input stream is not open.")

        data = self.file_handle.read(count)
        if not data:
            self.exhausted = True
        return data

    def is_connected(self) -> bool:
        return self.connected

    def is_exhausted(self) -> bool:
        return self.exhausted


FileInputByteStream = ioFileInputByteStream
