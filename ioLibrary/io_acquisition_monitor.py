from .io_byte_count_monitor_base import ioByteCountMonitorBase


class ioAcquisitionMonitor(ioByteCountMonitorBase):
    def record_read(self, nbytes: int) -> None:
        self._record_bytes(nbytes)

    @property
    def total_read(self) -> int:
        return self._get_total_count()


AcquisitionMonitor = ioAcquisitionMonitor
