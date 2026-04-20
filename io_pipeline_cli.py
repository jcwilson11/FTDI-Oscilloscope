from __future__ import annotations

import sys
import time

from ftd2xx_wrapper import FtdiError
from ioLibrary import PipelineConfig, PipelineController


class ioPipelineCli:
    def __init__(self, *, pipeline_controller_cls=PipelineController):
        self.pipeline_controller_cls = pipeline_controller_cls

    def build_config(self, args) -> PipelineConfig:
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

    def run(self, args) -> int:
        pipeline = None
        try:
            config = self.build_config(args)
            pipeline = self.pipeline_controller_cls(config)
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
