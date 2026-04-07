from dataclasses import dataclass


@dataclass
class ioAcquisitionConfig:
    input_hz: float = 10.0
    bytes_per_read: int = 8


AcquisitionConfig = ioAcquisitionConfig
