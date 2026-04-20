from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class ioViewportState:
    start_index: int = 0
    window_size: int = 200

    def to_dict(self) -> dict[str, int]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict | None) -> "ioViewportState":
        if not isinstance(payload, dict):
            return cls()

        state = cls()
        for field_name in state.to_dict():
            if field_name in payload:
                setattr(state, field_name, payload[field_name])
        return state
