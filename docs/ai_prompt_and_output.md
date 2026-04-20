# AI Prompt And Output

## Prompt Given To Codex
The implementation prompt provided to Codex required:
- a Qt-based MVC redesign with one abstract View and two selectable concrete Qt UIs
- strict one-class-per-file organization with `io<ClassName>` naming
- inheritance-based FTDI/file stream specializations with no duplicated responsibilities
- preservation of the scale/shift pipe-and-filter design
- preservation of the multithreaded circular-buffer FTDI transfer path
- 4+1 architectural documentation plus a readable class diagram
- compatibility with the existing `dev` branch baseline instead of a wholesale branch replacement
- incorporation of the earlier `origin/oscilloscope` UI scaffold as historical input rather than the canonical final architecture

## Output Produced
- Added `scope-qt` as the primary GUI launcher.
- Added `ioCompactOscilloscopeView`, `ioDetailedOscilloscopeView`, `ioQtScopeWindow`, and `ioFtdiWaveformSource`.
- Added `ioLiveOscilloscopeSession` and its live byte-stream helpers to keep live acquisition separate from the MVC view classes.
- Refactored `ioOscilloscopeView` into an abstract View contract.
- Preserved and reused the `ioLibrary` inheritance hierarchy for FTDI/file streams and multithreaded transfer workers.
- Updated controller, model, settings state, and tests to match the new canonical architecture.
- Added the PlantUML diagram set and the architecture document in `docs/architecture/`.

## Changes Made After The Initial AI Implementation
- The Qt classes were made import-safe for environments where `PySide6` and `pyqtgraph` are not installed.
- The controller was updated to fan out render state to both concrete view instances while tracking the active visible view.
- The oscilloscope source selection was extended to support FTDI-backed acquisition through `ioFtdiWaveformSource`.
- The FTDI adapter surface was aligned with the `io<ClassName>` rule through canonical `ioFtdiDevice` naming plus a preserved `FtdiDevice` alias.
- The documentation was rewritten to align the professor-facing design narrative with the implemented class structure.
