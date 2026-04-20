from typing import Protocol, runtime_checkable


@runtime_checkable
class ioStreamLifecycle(Protocol):
    def open(self) -> None:
        ...

    def close(self) -> None:
        ...

    def is_connected(self) -> bool:
        ...


StreamLifecycle = ioStreamLifecycle
