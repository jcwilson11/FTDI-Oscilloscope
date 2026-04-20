from __future__ import annotations

import tkinter as tk

from .io_view_theme import ioViewTheme


class ioTkOscilloscopeWindow:
    """Tkinter-backed oscilloscope window used by the live demo shell."""

    def __init__(self, theme: ioViewTheme, *, master: tk.Misc, title: str):
        self.theme = theme
        self.master = master
        self.title = title
        self.window = tk.Toplevel(master)
        self.window.title(title)
        self.window.configure(bg=self.theme.getPalette()["background"])
        self.window.protocol("WM_DELETE_WINDOW", self.window.withdraw)

        self._actions: dict[str, object] = {}
        self._widgets_ready = False
        self._viewport_change_in_progress = False

    def set_actions(self, actions: dict[str, object]) -> None:
        self._actions = dict(actions)
        if self._widgets_ready:
            self._bind_actions()

    def render(self, snapshot: dict) -> None:
        if not self._widgets_ready:
            self._build_widgets(snapshot)

        palette = snapshot["palette"]
        self.window.configure(bg=palette["background"])
        self.header_label.configure(
            text=(
                f"{snapshot['theme_name'].title()} view | "
                f"input={snapshot['input_source']} | "
                f"scale={snapshot['scale']:.2f} | offset={snapshot['offset']:.2f}"
            ),
            bg=palette["background"],
            fg=palette["text"],
        )
        self.status_label.configure(
            text=(
                f"samples={snapshot['sample_count']} | "
                f"window={snapshot['viewport_start']}:{snapshot['viewport_start'] + snapshot['viewport_window_size']} | "
                f"running={snapshot['running']}"
            ),
            bg=palette["background"],
            fg=palette["text"],
        )
        self._draw_signal(snapshot["visible_signal"], palette)
        self._update_viewport_scale(snapshot)

    def schedule(self, callback) -> None:
        self.master.after(0, callback)

    def mainloop(self) -> None:
        self.master.mainloop()

    def destroy(self) -> None:
        self.master.destroy()

    def _build_widgets(self, snapshot: dict) -> None:
        palette = snapshot["palette"]
        orientation = snapshot["orientation"]

        self.header_label = tk.Label(self.window, anchor="w", font=("Segoe UI", 11, "bold"))
        self.status_label = tk.Label(self.window, anchor="w", font=("Segoe UI", 10))
        self.canvas = tk.Canvas(
            self.window,
            width=640,
            height=280,
            highlightthickness=0,
            bg=palette["panel"],
        )
        self.viewport_scale = tk.Scale(
            self.window,
            from_=0,
            to=0,
            orient=tk.HORIZONTAL,
            showvalue=True,
            label="Scroll Window",
            command=self._on_viewport_changed,
        )
        self.button_bar = tk.Frame(self.window, bg=palette["background"])

        buttons = [
            ("scroll_left", "Scroll -"),
            ("scroll_right", "Scroll +"),
            ("scale_down", "Scale -"),
            ("scale_up", "Scale +"),
            ("offset_down", "Offset -"),
            ("offset_up", "Offset +"),
            ("refresh", "Refresh"),
        ]
        self.buttons = {}
        for action_name, label in buttons:
            button = tk.Button(self.button_bar, text=label, width=10)
            self.buttons[action_name] = button

        pad = {"padx": 8, "pady": 6}
        self.header_label.pack(fill=tk.X, **pad)
        self.status_label.pack(fill=tk.X, **pad)
        if orientation == "portrait":
            self.canvas.pack(fill=tk.BOTH, expand=True, **pad)
            self.viewport_scale.pack(fill=tk.X, **pad)
            self.button_bar.pack(fill=tk.X, **pad)
            for button in self.buttons.values():
                button.pack(fill=tk.X, pady=2)
        else:
            content = tk.Frame(self.window, bg=palette["background"])
            content.pack(fill=tk.BOTH, expand=True, **pad)
            self.canvas.pack(in_=content, side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
            controls = tk.Frame(content, bg=palette["background"])
            controls.pack(side=tk.RIGHT, fill=tk.Y)
            self.viewport_scale.pack(in_=controls, fill=tk.X, pady=(0, 8))
            self.button_bar.pack(in_=controls, fill=tk.X)
            for button in self.buttons.values():
                button.pack(side=tk.TOP, fill=tk.X, pady=2)

        self._widgets_ready = True
        self._bind_actions()

    def _bind_actions(self) -> None:
        for action_name, button in self.buttons.items():
            callback = self._actions.get(action_name)
            if callback is None:
                button.configure(command=lambda: None)
            else:
                button.configure(command=callback)

    def _draw_signal(self, signal: list[float], palette: dict[str, str]) -> None:
        self.canvas.delete("all")
        width = int(self.canvas["width"])
        height = int(self.canvas["height"])
        mid_y = height / 2.0

        for x in range(0, width, 40):
            self.canvas.create_line(x, 0, x, height, fill=palette["grid"])
        for y in range(0, height, 40):
            self.canvas.create_line(0, y, width, y, fill=palette["grid"])

        if len(signal) < 2:
            return

        points = []
        max_index = max(len(signal) - 1, 1)
        for index, sample in enumerate(signal):
            x = (index / max_index) * width
            y = mid_y - (sample * (height * 0.35))
            points.extend([x, y])

        self.canvas.create_line(points, fill=palette["signal"], width=2, smooth=True)

    def _update_viewport_scale(self, snapshot: dict) -> None:
        max_start = max(0, snapshot["sample_count"] - snapshot["viewport_window_size"])
        self._viewport_change_in_progress = True
        self.viewport_scale.configure(to=max_start)
        self.viewport_scale.set(snapshot["viewport_start"])
        self._viewport_change_in_progress = False

    def _on_viewport_changed(self, value: str) -> None:
        if self._viewport_change_in_progress:
            return
        callback = self._actions.get("set_viewport")
        if callback is not None:
            callback(int(float(value)))
