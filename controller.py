import argparse
import sys

from ftd2xx_wrapper import FtdiError
from ioLibrary import PipelineConfig, PipelineController

from io_file_comparator import ioFileComparator
from io_legacy_ftdi_cli import ioLegacyFtdiCli
from io_pipeline_cli import ioPipelineCli


_LEGACY_CLI = ioLegacyFtdiCli()


def write_message(device, message: str, pin_mask: int = 0x01):
    _LEGACY_CLI.write_message(device, message, pin_mask=pin_mask)


def prompt_int(prompt: str, minimum: int, maximum: int) -> int:
    return _LEGACY_CLI.prompt_int(prompt, minimum, maximum)


def control_leds(device):
    _LEGACY_CLI.control_leds(device)


def interactive_menu(device):
    _LEGACY_CLI.interactive_menu(device)


def build_pipeline_config(args: argparse.Namespace) -> PipelineConfig:
    return ioPipelineCli(pipeline_controller_cls=PipelineController).build_config(args)


def run_pipeline_command(args: argparse.Namespace) -> int:
    return ioPipelineCli(pipeline_controller_cls=PipelineController).run(args)


def compare_files(left_path: str, right_path: str, chunk_size: int = 4096) -> tuple[bool, str]:
    return ioFileComparator().compare_files(left_path, right_path, chunk_size=chunk_size)


def run_compare_files_command(args: argparse.Namespace) -> int:
    return ioFileComparator().run(args)


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

    scope_parser = subparsers.add_parser(
        "scope-shell",
        help="Run scilloscope shell",
    )
    scope_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run the shell without opening any GUI surfaces",
    )

    scope_qt_parser = subparsers.add_parser(
        "scope-qt",
        help="Run the Qt oscilloscope UI",
    )
    scope_qt_parser.add_argument(
        "--headless",
        action="store_true",
        help="Build the Qt architecture without opening a visual window",
    )

    return parser


def run_legacy_command(args: argparse.Namespace) -> int:
    return _LEGACY_CLI.run(args)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "pipeline":
            return run_pipeline_command(args)
        if args.command == "compare-files":
            return run_compare_files_command(args)
        if args.command == "scope-shell":
            from io_scope_shell import ioScopeShell

            return ioScopeShell(headless=args.headless).run_interactive()
        if args.command == "scope-qt":
            from io_scope_qt import run_scope_qt

            return run_scope_qt(headless=args.headless)
        return run_legacy_command(args)
    except FtdiError as exc:
        print(f"FTDI error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
