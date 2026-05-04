# ioScope Runtime Component Diagram Set

This runtime view now has one full overview plus three smaller companion diagrams.

1. Full runtime overview
   File: `docs/plantuml/io_scope_runtime_component.puml`
   Purpose: Shows the end-to-end runtime picture in one place.

2. Startup, settings, and UI host
   File: `docs/plantuml/io_scope_runtime_component_startup_ui.puml`
   Purpose: Shows how `controller.py`, `run_scope_qt`, `ioScopeShell`, the settings store, the Qt host window, and the two views are wired together.

3. Preview signal path
   File: `docs/plantuml/io_scope_runtime_component_preview_path.puml`
   Purpose: Shows the non-live sample path through `ioOscilloscopeModel`, `ioWaveformGenerator`, and the preview waveform sources.

4. Live session and transport
   File: `docs/plantuml/io_scope_runtime_component_live_transport.puml`
   Purpose: Shows the live acquisition path through `ioLiveOscilloscopeSession`, `ioPipelineController`, the read/write workers, and the shared buffer.
