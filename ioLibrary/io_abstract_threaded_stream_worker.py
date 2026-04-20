from __future__ import annotations

from abc import ABC

from .io_threaded_worker_base import ioThreadedWorkerBase


class ioAbstractThreadedStreamWorker(ioThreadedWorkerBase, ABC):
    def _prepare_start(self) -> None:
        if not self.stream.is_connected():
            self.stream.open()

    def _cleanup_after_run(self) -> None:
        if self.stream.is_connected():
            self.stream.close()


AbstractThreadedStreamWorker = ioAbstractThreadedStreamWorker
