from __future__ import annotations

import json
from pathlib import Path

from .io_control_state import ioControlState
from .io_viewport_state import ioViewportState


class ioScopeSettingsStore:
    """Loads and saves oscilloscope demo settings in a repo-root JSON file."""

    def __init__(self, path: str | Path | None = None):
        if path is None:
            path = Path(__file__).resolve().parent.parent / "io_scope_settings.json"
        self.path = Path(path)

    def load(self) -> dict[str, dict]:
        default_payload = self.default_payload()
        try:
            raw_payload = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return default_payload
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return default_payload

        if not isinstance(raw_payload, dict):
            return default_payload

        return {
            "control_state": ioControlState.from_dict(raw_payload.get("control_state")).to_dict(),
            "viewport_state": ioViewportState.from_dict(raw_payload.get("viewport_state")).to_dict(),
            "event_log": self._normalize_event_log(raw_payload.get("event_log")),
        }

    def save(self, payload: dict[str, dict]) -> None:
        normalized_payload = {
            "control_state": ioControlState.from_dict(payload.get("control_state")).to_dict(),
            "viewport_state": ioViewportState.from_dict(payload.get("viewport_state")).to_dict(),
            "event_log": self._normalize_event_log(payload.get("event_log")),
        }
        self.path.write_text(json.dumps(normalized_payload, indent=2), encoding="utf-8")

    def default_payload(self) -> dict[str, dict]:
        return {
            "control_state": ioControlState().to_dict(),
            "viewport_state": ioViewportState().to_dict(),
            "event_log": [],
        }

    def _normalize_event_log(self, payload: object) -> list[dict]:
        if not isinstance(payload, list):
            return []
        return [entry for entry in payload if isinstance(entry, dict)]
