import argparse
import time

from ioLibrary import ioBuffer, ioRead, ioWrite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FTDI LED blink demo using ioLibrary")
    parser.add_argument("--dll", help="Optional path to ftd2xx.dll")
    parser.add_argument("--device-index", type=int, default=0, help="FTDI device index")
    parser.add_argument(
        "--cycles",
        type=int,
        default=4,
        help="Number of alternating write cycles to run at each frequency",
    )
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=1.0,
        help="Pause between the 1 Hz and 2 Hz demo segments",
    )
    return parser


def create_io_objects(dll_path: str | None, device_index: int):
    shared_buffer = ioBuffer(2)
    shared_buffer.write([0xFF, 0x00])
    reader = ioRead(dll_path=dll_path, device_index=device_index)
    writer = ioWrite(dll_path=dll_path, device_index=device_index)

    reader.setBuffer(shared_buffer).setN(2)
    writer.setBuffer(shared_buffer).setM(2)
    return shared_buffer, reader, writer


def run_segment(writer: ioWrite, frequency_hz: float, cycles: int):
    writer.setFrequency(frequency_hz)

    print(
        f"Starting blink segment at {frequency_hz:.0f} Hz with pattern [0xFF, 0x00]; "
        f"each state is held for {writer.element_interval_seconds:.2f} seconds"
    )
    writer.executeWrite(cycles=cycles, sequence_mode=True)
    print(f"Completed {cycles} cycles at {frequency_hz:.0f} Hz")


def main() -> int:
    args = build_parser().parse_args()
    _, reader, writer = create_io_objects(args.dll, args.device_index)

    print("ioLibrary LED blink demo")
    print(
        "Configured ioRead and ioWrite with a shared ioBuffer in MainApp; "
        "the demo executes the writer path for LED blinking."
    )
    print("Segment 1: 1 Hz")
    reader.setFrequency(1.0)
    run_segment(writer, 1.0, args.cycles)
    time.sleep(max(args.pause_seconds, 0.0))
    print("Segment 2: 2 Hz")
    reader.setFrequency(2.0)
    run_segment(writer, 2.0, args.cycles)
    print("Demo complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
