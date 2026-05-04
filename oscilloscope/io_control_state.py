from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class ioControlState:
    sample_time_seconds: float = 0.001
    sample_duration_seconds: float = 1.0
    input_source: str = "sine"
    generated_waveform: str = "sine"
    live_file_path: str = "demo_input.bin"
    scale: float = 1.0
    offset: float = 0.0
    active_theme: str = "portrait"
    active_view: str = "compact"
    ftdi_input_device_index: int = 0
    ftdi_input_bit_index: int = 0
    ftdi_output_device_index: int = 0
    ftdi_bytes_per_read: int = 256
    ftdi_dll_path: str = ""
    write_to_ftdi_enabled: bool = False
    tee_output_enabled: bool = False
    tee_output_mode: str = "none"
    tee_output_path: str = "demo_output.bin"
    render_interval_ms: int = 50

    def __post_init__(self) -> None:
        self._sync_derived_fields()

    def to_dict(self) -> dict[str, float | str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict | None) -> "ioControlState":
        if not isinstance(payload, dict):
            return cls()

        state = cls()
        for field_name in state.to_dict():
            if field_name in payload:
                setattr(state, field_name, payload[field_name])

        # Backward compatibility with older persisted tee flags.
        if payload.get("write_to_ftdi_enabled"):
            state.tee_output_enabled = True
            state.tee_output_mode = "ftdi"
            state.write_to_ftdi_enabled = True

        state._sync_derived_fields()
        return state

    def _sync_derived_fields(self) -> None:
        if self.input_source.startswith("file:"):
            self.live_file_path = self.input_source[5:] or self.live_file_path
        elif self.input_source.startswith("ftdi:"):
            raw_index = self.input_source.split(":", 1)[1].strip()
            if raw_index:
                self.ftdi_input_device_index = int(raw_index)
        elif self.input_source in {"sine", "square", "triangle", "sawtooth"}:
            self.generated_waveform = self.input_source
