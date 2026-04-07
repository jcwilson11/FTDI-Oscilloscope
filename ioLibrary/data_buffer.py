from __future__ import annotations

import threading
import time
from typing import Optional


class ioDataBuffer:
    """Thread-safe bounded circular buffer shared by the read and write workers."""

    def __init__(self, capacity: int = 1024):
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")

        self.capacity = capacity
        self._storage = bytearray(capacity)
        self._head = 0
        self._tail = 0
        self._count = 0
        self._closed = False
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

    def push(self, data: bytes) -> None:
        if not data:
            return

        payload = memoryview(bytes(data))
        offset = 0
        with self._lock:
            while offset < len(payload):
                while self._count >= self.capacity and not self._closed:
                    self._not_full.wait()

                if self._closed:
                    raise RuntimeError("Cannot push to closed buffer.")

                writable = min(self.capacity - self._count, len(payload) - offset)
                first = min(writable, self.capacity - self._tail)
                self._storage[self._tail : self._tail + first] = payload[offset : offset + first]
                self._tail = (self._tail + first) % self.capacity
                offset += first
                self._count += first

                second = writable - first
                if second:
                    self._storage[self._tail : self._tail + second] = payload[offset : offset + second]
                    self._tail = (self._tail + second) % self.capacity
                    offset += second
                    self._count += second

                self._not_empty.notify_all()

    def pop(self, n: int, timeout: Optional[float] = None) -> bytes:
        if n <= 0:
            return b""

        with self._lock:
            if timeout is None:
                while self._count == 0 and not self._closed:
                    self._not_empty.wait()
            else:
                end_time = time.perf_counter() + timeout
                while self._count == 0 and not self._closed:
                    remaining = end_time - time.perf_counter()
                    if remaining <= 0:
                        return b""
                    self._not_empty.wait(timeout=remaining)

            if self._count == 0 and self._closed:
                return b""

            readable = min(n, self._count)
            out = bytearray(readable)
            first = min(readable, self.capacity - self._head)
            out[:first] = self._storage[self._head : self._head + first]
            self._head = (self._head + first) % self.capacity
            self._count -= first

            second = readable - first
            if second:
                out[first:] = self._storage[self._head : self._head + second]
                self._head = (self._head + second) % self.capacity
                self._count -= second

            self._not_full.notify_all()
            return bytes(out)

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._not_empty.notify_all()
            self._not_full.notify_all()

    def is_closed(self) -> bool:
        with self._lock:
            return self._closed

    def is_empty(self) -> bool:
        with self._lock:
            return self._count == 0

    def is_full(self) -> bool:
        with self._lock:
            return self._count == self.capacity

    def size(self) -> int:
        with self._lock:
            return self._count

    def available_space(self) -> int:
        with self._lock:
            return self.capacity - self._count


DataBuffer = ioDataBuffer
