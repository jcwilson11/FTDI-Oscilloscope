from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import Optional


class ioThreadedWorkerBase(ABC):
    def __init__(self):
        self.running = False
        self.thread: threading.Thread | None = None
        self.lock = threading.Lock()

    def start(self) -> None:
        with self.lock:
            if self.running:
                return
            self.running = True

        self._prepare_start()
        self.thread = threading.Thread(target=self._run_worker_entry, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        with self.lock:
            self.running = False

        if self.thread is not None:
            self.thread.join(timeout=2.0)
            self._after_stop_joined()
        else:
            self._handle_stop_without_thread()

    def join(self, timeout: Optional[float] = None) -> None:
        if self.thread is not None:
            self.thread.join(timeout=timeout)

    def is_running(self) -> bool:
        with self.lock:
            return self.running

    def _run_worker_entry(self) -> None:
        try:
            self._run_worker()
        finally:
            try:
                self._cleanup_after_run()
            finally:
                with self.lock:
                    self.running = False

    def _prepare_start(self) -> None:
        pass

    def _after_stop_joined(self) -> None:
        pass

    def _handle_stop_without_thread(self) -> None:
        pass

    def _cleanup_after_run(self) -> None:
        pass

    @abstractmethod
    def _run_worker(self) -> None:
        raise NotImplementedError


ThreadedWorkerBase = ioThreadedWorkerBase
