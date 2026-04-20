# ioScope Requirements

## Functional Requirements

- `REQ-01` The repository shall compile on the instructor machine with `python -m compileall controller.py io_scope_qt.py io_scope_shell.py ioLibrary oscilloscope tests`.
- `REQ-02` The repository shall run its automated verification suite with `pytest -q`.
- `REQ-03` The repository shall expose a professor-facing Qt oscilloscope launcher through `python controller.py scope-qt`.
- `REQ-04` The repository shall preserve the professor-facing shell through `python controller.py scope-shell`.
- `REQ-05` The oscilloscope application layer shall preserve MVC responsibilities: model owns state and processed data, controller owns orchestration, and view owns rendering and user input only.
- `REQ-06` The system shall provide two selectable Qt user interfaces through `ioCompactOscilloscopeView` and `ioDetailedOscilloscopeView`.
- `REQ-07` The two concrete Qt views shall inherit one abstract `ioOscilloscopeView` contract.
- `REQ-08` Scale and offset changes shall execute only through `ioFilterPipeline`.
- `REQ-09` The oscilloscope shall support deterministic generated waveforms: `sine`, `square`, `triangle`, and `sawtooth`.
- `REQ-10` The oscilloscope shall support deterministic file-backed sample input through `input=file:<path>`.
- `REQ-11` The oscilloscope shall support FTDI-backed sample input through `input=ftdi` or `input=ftdi:<index>`.
- `REQ-12` The multithreaded FTDI pipeline shall remain available through `python controller.py pipeline ...`.
- `REQ-13` The multithreaded pipeline shall preserve the producer-consumer path `ioPipelineController -> ioUsbReadController -> ioDataBuffer -> ioUsbWriteController`.
- `REQ-14` The circular buffer shall preserve bounded, thread-safe, FIFO semantics with close-and-drain behavior.
- `REQ-15` Professor-visible code shall use canonical `io<ClassName>` class/file names, with compatibility shims allowed only as thin re-exports.
- `REQ-15A` Legacy names may remain only as compatibility aliases when the canonical implementation already follows the `io<ClassName>` convention.

## Structural Requirements

- `REQ-16` Each canonical class shall live in its own file.
- `REQ-17` Shared readable-stream behavior shall live in the readable base hierarchy.
- `REQ-18` Shared writable-stream behavior shall live in the writable base hierarchy.
- `REQ-19` FTDI-specific behavior shall live only in FTDI subclasses.
- `REQ-20` File-specific behavior shall live only in file subclasses.
- `REQ-21` The controller shall fan out the same processed sample state to both concrete view instances.
- `REQ-22` Runtime settings shall persist in JSON so source, scale, offset, theme, FTDI settings, and active view can be reloaded.
- `REQ-23` The design artifacts shall include package, logical class, readable class, process, development, physical, and scenario views.
- `REQ-24` The logical class diagrams shall include implemented live-session support classes in addition to the core MVC and FTDI pipeline classes.

## Demo Commands

```powershell
python -m compileall controller.py io_scope_qt.py io_scope_shell.py ioLibrary oscilloscope tests
pytest -q
python controller.py scope-qt --headless
python controller.py scope-shell
```
