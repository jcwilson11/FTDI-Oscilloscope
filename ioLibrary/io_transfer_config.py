from dataclasses import dataclass


@dataclass
class ioTransferConfig:
    output_hz: float = 10.0
    bytes_per_write: int = 8


TransferConfig = ioTransferConfig
