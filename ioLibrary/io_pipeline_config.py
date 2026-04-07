from dataclasses import dataclass


@dataclass
class ioPipelineConfig:
    input_mode: str = "ftdi"
    input_device_index: int = 0
    input_path: str | None = None
    output_mode: str = "file"
    output_path: str | None = None
    output_device_index: int | None = None
    append_output: bool = True
    bytes_per_read: int = 8
    bytes_per_write: int = 8
    input_hz: float = 10.0
    output_hz: float = 10.0
    buffer_capacity: int = 1024
    dll_path: str | None = None

    def __post_init__(self) -> None:
        if self.input_mode not in {"file", "ftdi"}:
            raise ValueError("input_mode must be 'file' or 'ftdi'")
        if self.input_mode == "file" and not self.input_path:
            raise ValueError("file input mode requires input_path")
        if self.output_mode not in {"file", "ftdi"}:
            raise ValueError("output_mode must be 'file' or 'ftdi'")
        if self.output_mode == "file" and not self.output_path:
            raise ValueError("file output mode requires output_path")
        if self.output_mode == "ftdi" and self.output_device_index is None:
            raise ValueError("ftdi output mode requires output_device_index")
        if self.bytes_per_read <= 0 or self.bytes_per_write <= 0:
            raise ValueError("chunk sizes must be greater than zero")
        if self.input_hz <= 0 or self.output_hz <= 0:
            raise ValueError("input_hz and output_hz must be greater than zero")
        if self.buffer_capacity <= 0:
            raise ValueError("buffer_capacity must be greater than zero")
        if self.buffer_capacity < max(self.bytes_per_read, self.bytes_per_write):
            raise ValueError("buffer_capacity must be at least the largest chunk size")


PipelineConfig = ioPipelineConfig
