from typing import Protocol, runtime_checkable


@runtime_checkable
class ioOscilloscopeWindow(Protocol):
    def set_actions(self, actions: dict[str, object]) -> None:
        ...

    def render(self, snapshot: dict) -> None:
        ...

    def schedule(self, callback) -> None:
        ...

    def mainloop(self) -> None:
        ...

    def destroy(self) -> None:
        ...


OscilloscopeWindow = ioOscilloscopeWindow
