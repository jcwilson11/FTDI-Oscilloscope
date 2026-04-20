from __future__ import annotations

import sys
from pathlib import Path


class ioFileComparator:
    def compare_files(self, left_path: str, right_path: str, chunk_size: int = 4096) -> tuple[bool, str]:
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

    def run(self, args) -> int:
        try:
            matches, message = self.compare_files(args.left_file, args.right_file)
        except (FileNotFoundError, ValueError) as exc:
            print(f"Compare error: {exc}", file=sys.stderr)
            return 1

        print(message)
        return 0 if matches else 1
