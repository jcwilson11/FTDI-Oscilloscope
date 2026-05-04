from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .io_landscape_theme import ioLandscapeTheme
from .io_render_state import ioRenderState
from .io_view_theme import ioViewTheme


class ioOscilloscopeView(ABC):
    """Abstract MVC View boundary for oscilloscope user interfaces."""

    def __init__(
        self,
        *,
        view_id: str,
        title: str,
        theme: ioViewTheme | None = None,
        canvas: str = "Canvas",
        controls: str = "ControlPanel",
    ):
        self.view_id = view_id
        self.title = title
        self.theme = theme if theme is not None else ioLandscapeTheme()
        self.canvas = canvas
        self.controls = controls
        self.controller: Any | None = None
        self.actions: dict[str, object] = {}
        self.lastRenderedSignal: list[float] = []
        self.lastRenderState: ioRenderState | None = None
        self.lastSnapshot: dict[str, Any] | None = None

    def connectController(self, controller: Any) -> None:
        self.controller = controller

    def attachActions(self, actions: dict[str, object]) -> None:
        self.actions = dict(actions)
        self._handle_actions_updated()

    def setTheme(self, theme: ioViewTheme) -> None:
        self.theme = theme
        self._handle_theme_updated()

    def render(self, render_input: ioRenderState | list[float]) -> dict[str, Any]:
        snapshot = self._build_snapshot(render_input)
        self.lastSnapshot = snapshot
        self.lastRenderedSignal = list(snapshot["signal"])
        self.lastRenderState = render_input if isinstance(render_input, ioRenderState) else None
        self._render_snapshot(snapshot)
        return snapshot

    def _build_snapshot(self, render_input: ioRenderState | list[float]) -> dict[str, Any]:
        if isinstance(render_input, ioRenderState):
            return {
                "view_id": self.view_id,
                "view_title": self.title,
                "canvas": render_input.canvas,
                "controls": render_input.controls,
                "theme_name": render_input.theme_name,
                "orientation": render_input.orientation,
                "palette": dict(render_input.palette),
                "input_source": render_input.input_source,
                "scale": render_input.scale,
                "offset": render_input.offset,
                "sample_time_seconds": render_input.sample_time_seconds,
                "sample_duration_seconds": render_input.sample_duration_seconds,
                "raw_signal": list(render_input.raw_signal),
                "processed_signal": list(render_input.processed_signal),
                "signal": list(render_input.visible_signal),
                "visible_signal": list(render_input.visible_signal),
                "viewport_start": render_input.viewport_start,
                "viewport_window_size": render_input.viewport_window_size,
                "sample_count": render_input.sample_count,
                "running": render_input.running,
                "active_view": render_input.active_view,
                "ftdi_input_bit_index": render_input.ftdi_input_bit_index,
                "session_mode": render_input.session_mode,
                "tee_output_mode": render_input.tee_output_mode,
                "bytes_read": render_input.bytes_read,
                "bytes_written": render_input.bytes_written,
                "buffer_size": render_input.buffer_size,
                "safe_stopped": render_input.safe_stopped,
            }

        return {
            "view_id": self.view_id,
            "view_title": self.title,
            "canvas": self.canvas,
            "controls": self.controls,
            "theme_name": self.theme.getName(),
            "orientation": self.theme.getOrientation(),
            "palette": self.theme.getPalette(),
            "signal": list(render_input),
            "visible_signal": list(render_input),
            "sample_count": len(render_input),
            "active_view": self.view_id,
        }

    @abstractmethod
    def _render_snapshot(self, snapshot: dict[str, Any]) -> None:
        raise NotImplementedError

    def _handle_actions_updated(self) -> None:
        """Hook for concrete UI implementations to bind controller actions."""

    def _handle_theme_updated(self) -> None:
        """Hook for concrete UI implementations to refresh their palette."""
