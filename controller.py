import argparse
import sys
import time

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
        input_device_index=args.input_device_index,
        output_mode=args.output_mode,
        output_path=args.output_path,
        output_device_index=args.output_device_index,
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
        while time.perf_counter() < deadline:
            remaining = deadline - time.perf_counter()
            time.sleep(min(0.1, max(remaining, 0.0)))
            snapshot = pipeline.status_snapshot()
            if snapshot["safe_stopped"] and not pipeline.is_running():
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
        "--output-mode",
        choices=["file", "ftdi"],
        required=True,
        help="Pipeline output destination type",
    )
    pipeline_parser.add_argument("--output-path", help="Output file path for file mode")
    pipeline_parser.add_argument("--output-device-index", type=int, help="FTDI destination device index for ftdi mode")
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
        return run_legacy_command(args)
    except FtdiError as exc:
        print(f"FTDI error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
