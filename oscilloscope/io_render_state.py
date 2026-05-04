from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ioRenderState:
    view_id: str
    view_title: str
    canvas: str
    controls: str
    theme_name: str
    orientation: str
    palette: dict[str, str]
    input_source: str
    scale: float
    offset: float
    sample_time_seconds: float
    sample_duration_seconds: float
    raw_signal: list[float]
    processed_signal: list[float]
    visible_signal: list[float]
    viewport_start: int
    viewport_window_size: int
    sample_count: int
    running: bool
    active_view: str
    ftdi_input_bit_index: int = 0
    session_mode: str = "idle"
    tee_output_mode: str = "none"
    bytes_read: int = 0
    bytes_written: int = 0
    buffer_size: int = 0
    safe_stopped: bool = False
