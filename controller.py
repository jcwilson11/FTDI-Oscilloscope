import argparse
import sys
import time
from pathlib import Path

from ftd2xx_wrapper import FtdiDevice, FtdiError
from ioLibrary import PipelineConfig, PipelineController


MORSE_CODE = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
}


def write_message(device: FtdiDevice, message: str, pin_mask: int = 0x01):
    unit_seconds = 0.1
    for character in message:
        if character == " ":
            time.sleep(unit_seconds * 7)
            continue

        morse = MORSE_CODE.get(character.upper())
        if not morse:
            continue

        print(f"Morse code for '{character}': {morse}")
        for symbol in morse:
            device.write_byte(pin_mask)
            time.sleep(unit_seconds if symbol == "." else unit_seconds * 3)
            device.write_byte(0x00)
            time.sleep(unit_seconds)
        time.sleep(unit_seconds * 2)


def prompt_int(prompt: str, minimum: int, maximum: int) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw, 0)
        except ValueError:
            print("Enter a valid integer.")
            continue

        if minimum <= value <= maximum:
            return value

        print(f"Enter a value between {minimum} and {maximum}.")


def control_leds(device: FtdiDevice):
    state = 0x00
    while True:
        raw = input("\nEnter pin 0-7, 'reset', or 'done': ").strip().lower()
        if raw == "done":
            break
        if raw == "reset":
            state = 0x00
            device.write_byte(state)
            print("All pins set to OFF.")
            continue

        try:
            pin = int(raw)
        except ValueError:
            print("Enter a pin number, 'reset', or 'done'.")
            continue

        if not 0 <= pin <= 7:
            print("Pin must be between 0 and 7.")
            continue

        for current_pin in range(8):
            pin_state = "ON" if state & (1 << current_pin) else "OFF"
            print(f"Pin {current_pin} = {pin_state}")

        new_value = prompt_int(f"Enter new state for pin {pin} (0 or 1): ", 0, 1)
        if new_value:
            state |= 1 << pin
        else:
            state &= ~(1 << pin)

        device.write_byte(state)
        print(f"Wrote 0x{state:02X}")


def interactive_menu(device: FtdiDevice):
    while True:
        print("\nControl Menu")
        print("1. Control LEDs")
        print("2. Send Morse Code")
        print("3. Write byte to port")
        print("4. Read byte from port")
        print("5. Exit")

        choice = input("Enter your choice: ").strip()
        if choice == "1":
            control_leds(device)
        elif choice == "2":
            message = input("Enter your message (blank line to cancel): ")
            if message:
                write_message(device, message)
        elif choice == "3":
            value = prompt_int("Enter byte value (0-255, hex allowed): ", 0, 255)
            device.write_byte(value)
            print(f"Wrote 0x{value:02X}")
        elif choice == "4":
            value = device.read_byte()
            print(f"Read 1 byte: 0x{value:02X}")
        elif choice == "5":
            return
        else:
            print("Invalid choice.")


def build_pipeline_config(args: argparse.Namespace) -> PipelineConfig:
    if args.duration_seconds <= 0:
        raise ValueError("--duration-seconds must be greater than zero")

    return PipelineConfig(
        input_mode=args.input_mode,
        input_device_index=args.input_device_index,
        input_path=args.input_path,
        output_mode=args.output_mode,
        output_path=args.output_path,
        output_device_index=args.output_device_index,
        append_output=not args.overwrite_output,
        bytes_per_read=args.bytes_per_read,
        bytes_per_write=args.bytes_per_write,
        input_hz=args.input_hz,
        output_hz=args.output_hz,
        buffer_capacity=args.buffer_capacity,
        dll_path=args.dll,
    )


def run_pipeline_command(args: argparse.Namespace) -> int:
    pipeline = None
    try:
        config = build_pipeline_config(args)
        pipeline = PipelineController(config)
        pipeline.start()

        deadline = time.perf_counter() + args.duration_seconds
        next_status_time = time.perf_counter()
        while time.perf_counter() < deadline:
            remaining = deadline - time.perf_counter()
            time.sleep(min(0.1, max(remaining, 0.0)))
            snapshot = pipeline.status_snapshot()
            now = time.perf_counter()
            if now >= next_status_time:
                print(
                    "Running...",
                    f"buffer={snapshot['buffer_size']}/{snapshot['buffer_capacity']}",
                    f"read={snapshot['bytes_read']}",
                    f"written={snapshot['bytes_written']}",
                )
                next_status_time = now + 0.5
            if not pipeline.is_running() and (snapshot["safe_stopped"] or snapshot["buffer_closed"]):
                break

        return_code = 0
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return_code = 130
    except (FtdiError, RuntimeError, ValueError) as exc:
        print(f"Pipeline error: {exc}", file=sys.stderr)
        return 1
    finally:
        if pipeline is not None:
            pipeline.stop()

    snapshot = pipeline.status_snapshot()
    print("Pipeline stopped.")
    print("Output mode:", snapshot["output_mode"])
    print("Bytes read:", snapshot["bytes_read"])
    print("Bytes written:", snapshot["bytes_written"])
    print("Read throughput KB/s:", round(snapshot["read_throughput_kbps"], 3))
    print("Write throughput KB/s:", round(snapshot["write_throughput_kbps"], 3))
    print("Buffer size:", snapshot["buffer_size"])
    print("Recovery safe stop:", snapshot["safe_stopped"])
    if snapshot["recovery_messages"]:
        print("Recovery messages:")
        for message in snapshot["recovery_messages"]:
            print("-", message)

    if snapshot["safe_stopped"] and return_code == 0:
        return 1
    return return_code


def compare_files(left_path: str, right_path: str, chunk_size: int = 4096) -> tuple[bool, str]:
    left = Path(left_path)
    right = Path(right_path)

    if not left.exists():
        raise FileNotFoundError(f"Left file not found: {left}")
    if not right.exists():
        raise FileNotFoundError(f"Right file not found: {right}")
    if not left.is_file():
        raise ValueError(f"Left path is not a file: {left}")
    if not right.is_file():
        raise ValueError(f"Right path is not a file: {right}")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    offset = 0
    with left.open("rb") as left_handle, right.open("rb") as right_handle:
        while True:
            left_chunk = left_handle.read(chunk_size)
            right_chunk = right_handle.read(chunk_size)

            if left_chunk == right_chunk:
                if not left_chunk:
                    size = left.stat().st_size
                    return True, f"Files match exactly ({size} bytes)."
                offset += len(left_chunk)
                continue

            limit = min(len(left_chunk), len(right_chunk))
            for index in range(limit):
                if left_chunk[index] != right_chunk[index]:
                    absolute_offset = offset + index
                    return (
                        False,
                        "Files differ at byte offset "
                        f"{absolute_offset}: left=0x{left_chunk[index]:02X}, right=0x{right_chunk[index]:02X}.",
                    )

            return (
                False,
                "Files have different lengths starting at byte offset "
                f"{offset + limit}: left_size={left.stat().st_size}, right_size={right.stat().st_size}.",
            )


def run_compare_files_command(args: argparse.Namespace) -> int:
    try:
        matches, message = compare_files(args.left_file, args.right_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Compare error: {exc}", file=sys.stderr)
        return 1

    print(message)
    return 0 if matches else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Python FT245R controller")
    parser.add_argument("--dll", help="Optional path to ftd2xx.dll")
    parser.add_argument("--list-devices", action="store_true", help="List D2XX-visible FTDI devices and exit")
    parser.add_argument("--write", type=lambda value: int(value, 0), help="Write one byte and exit")
    parser.add_argument("--read", action="store_true", help="Read one byte and exit")
    parser.add_argument("--morse", help="Send a message as Morse code and exit")

    subparsers = parser.add_subparsers(dest="command")
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run the multithreaded FTDI data acquisition pipeline",
    )
    pipeline_parser.add_argument("--input-device-index", type=int, default=0, help="FTDI source device index")
    pipeline_parser.add_argument(
        "--input-mode",
        choices=["file", "ftdi"],
        default="ftdi",
        help="Pipeline input source type",
    )
    pipeline_parser.add_argument("--input-path", help="Input file path for file mode")
    pipeline_parser.add_argument(
        "--output-mode",
        choices=["file", "ftdi"],
        required=True,
        help="Pipeline output destination type",
    )
    pipeline_parser.add_argument("--output-path", help="Output file path for file mode")
    pipeline_parser.add_argument("--output-device-index", type=int, help="FTDI destination device index for ftdi mode")
    pipeline_parser.add_argument(
        "--overwrite-output",
        action="store_true",
        help="Overwrite the output file instead of appending to it",
    )
    pipeline_parser.add_argument("--bytes-per-read", type=int, default=8, help="Read chunk size")
    pipeline_parser.add_argument("--bytes-per-write", type=int, default=8, help="Write chunk size")
    pipeline_parser.add_argument("--input-hz", type=float, default=10.0, help="Read loop frequency in Hz")
    pipeline_parser.add_argument("--output-hz", type=float, default=10.0, help="Write loop frequency in Hz")
    pipeline_parser.add_argument("--buffer-capacity", type=int, default=1024, help="Circular buffer capacity in bytes")
    pipeline_parser.add_argument(
        "--duration-seconds",
        type=float,
        default=2.0,
        help="How long to run the pipeline before clean shutdown",
    )

    compare_parser = subparsers.add_parser(
        "compare-files",
        help="Compare two files byte-for-byte",
    )
    compare_parser.add_argument("left_file", help="First file to compare")
    compare_parser.add_argument("right_file", help="Second file to compare")

    return parser


def run_legacy_command(args: argparse.Namespace) -> int:
    listing_client = FtdiDevice(dll_path=args.dll)
    if args.list_devices:
        devices = listing_client.list_devices()
        if not devices:
            print("No FTDI devices visible through the D2XX driver.")
            return 0

        for device in devices:
            print(
                f"index={device['index']} serial={device['serial']} "
                f"description={device['description']} id=0x{device['id']:08X} "
                f"location=0x{device['location_id']:08X} flags=0x{device['flags']:08X}"
            )
        return 0

    with listing_client as device:
        if args.write is not None:
            if not 0 <= args.write <= 0xFF:
                raise FtdiError("--write value must be between 0 and 255")
            device.write_byte(args.write)
            print(f"Wrote 0x{args.write:02X}")
            return 0

        if args.read:
            value = device.read_byte()
            print(f"Read 1 byte: 0x{value:02X}")
            return 0

        if args.morse:
            write_message(device, args.morse)
            return 0

        interactive_menu(device)
        return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "pipeline":
            return run_pipeline_command(args)
        if args.command == "compare-files":
            return run_compare_files_command(args)
        return run_legacy_command(args)
    except FtdiError as exc:
        print(f"FTDI error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
