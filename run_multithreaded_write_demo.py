import time
from ioLibrary.multithreaded_write import (
    TransferConfig,
    ThroughputMonitor,
    RecoveryManager,
    OutputScheduler,
    DataBuffer,
    FileByteStream,
    UsbWriteController,
)


def main():
    cfg = TransferConfig(output_hz=10.0, bytes_per_write=4)
    buffer = DataBuffer(capacity=64)
    throughput_monitor = ThroughputMonitor()
    recovery_manager = RecoveryManager()
    scheduler = OutputScheduler()
    stream = FileByteStream("demo_output.bin")

    writer = UsbWriteController(
        stream=stream,
        cfg=cfg,
        buffer=buffer,
        throughput_monitor=throughput_monitor,
        recovery_manager=recovery_manager,
        scheduler=scheduler,
    )

    buffer.push(b"HelloFTDIPipelineDemo")

    writer.start()
    time.sleep(2)
    writer.stop()

    print("Writer stopped.")
    print("Total bytes written:", throughput_monitor.total_written)
    print("Throughput KB/s:", round(throughput_monitor.throughput_kbps(), 3))
    print("Recovery safe stop:", recovery_manager.safe_stopped)


if __name__ == "__main__":
    main()