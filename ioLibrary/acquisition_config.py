from dataclasses import dataclass


@dataclass
class AcquisitionConfig:
    input_hz: float = 10.0
    bytes_per_read: int = 8
