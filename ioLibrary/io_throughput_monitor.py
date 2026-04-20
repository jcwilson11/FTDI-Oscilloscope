from .io_byte_count_monitor_base import ioByteCountMonitorBase


class ioThroughputMonitor(ioByteCountMonitorBase):
    def record_write(self, nbytes: int) -> None:
        self._record_bytes(nbytes)

    @property
    def total_written(self) -> int:
        return self._get_total_count()


ThroughputMonitor = ioThroughputMonitor
