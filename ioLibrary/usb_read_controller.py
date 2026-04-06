import threading

from .acquisition_config import AcquisitionConfig
from .acquisition_monitor import AcquisitionMonitor
from .ftdi_byte_stream import FtdiByteStream
from .input_scheduler import InputScheduler
from .multithreaded_write import DataBuffer, RecoveryManager


class UsbReadController:
    def __init__(
        self,
        stream: FtdiByteStream,
        cfg: AcquisitionConfig,
        buffer: DataBuffer,
        acquisition_monitor: AcquisitionMonitor,
        recovery_manager: RecoveryManager,
        scheduler: InputScheduler,
    ):
        self.stream = stream
        self.cfg = cfg
        self.buffer = buffer
        self.acquisition_monitor = acquisition_monitor
        self.recovery_manager = recovery_manager
        self.scheduler = scheduler
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self) -> None:
        with self.lock:
            if self.running:
                return
            self.running = True

        if not self.stream.is_connected():
            self.stream.open()

        self.thread = threading.Thread(target=self.read_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        with self.lock:
            self.running = False

        if self.thread is not None:
            self.thread.join(timeout=2.0)

        self.stream.close()
        self.buffer.close()

    def is_running(self) -> bool:
        with self.lock:
            return self.running

    def read_loop(self) -> None:
        try:
            while self.is_running():
                if not self.stream.is_connected():
                    self.recovery_manager.notify_user("Input connection lost.")
                    self.recovery_manager.transition_to_safe_stop()
                    break

                data = self.stream.read_bytes(self.cfg.bytes_per_read)
                if data:
                    self.buffer.push(data)
                    self.acquisition_monitor.record_read(len(data))

                self.scheduler.sleep_until_next_input(self.cfg.input_hz)

        except Exception as exc:
            self.recovery_manager.notify_user(f"Read failure: {exc}")
            self.recovery_manager.transition_to_safe_stop()
        finally:
            self.buffer.close()
            self.stream.close()
            with self.lock:
                self.running = False
